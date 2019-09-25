'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404, 
    JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.shortcuts import redirect

from fg.apps.main.models import (
    Container, 
    Plate,
    Well
)

from fg.apps.factory.twist import (
    get_orders,
    get_client,
    get_unique_plates
)
from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import django_rq

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_orders(request):
    '''Show a table of twist orders for the user.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    # Returns empty list if no orders, or no credentials
    orders = get_orders()

    context = {"orders": orders}
    return render(request, 'twist/orders.html', context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_order(request, uuid):
    '''Show a single twist order based on its unique id, the sfsc_id
       If shipments are defined, then we also present an import table, 
       and request that the user define a name for each unique plate, 
       and container (location).
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    # Returns empty list if no orders, or no credentials
    items = []
    client = get_client()
    if client:
        items = client.order_items(uuid)

    context = {"items": items}
    return render(request, 'twist/order.html', context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_order_import(request, uuid):
    '''Make a request to import an order - must be done with
       django_rq since it's slow to download the platemaps.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")

    # We need to present the form to the user
    if request.method == "GET":

        # We need to derive the unique plates from the data
        plate_ids = get_unique_plates(uuid)
 
        if not plate_ids:
            messages.info(request, "Unable to retrieve client for Twist, consult with admin about API tokens.")
            return redirect('twist_order', uuid=uuid, user_id=request.user.id)

        context = {"order_id": uuid,
                   "plate_ids": plate_ids,
                   "plate_forms": Plate.PLATE_FORM,
                   "containers": Container.objects.all()}

        return render(request, 'twist/import_form.html', context)

    # The user has provided containers and plate names to import
    elif request.method == "POST":

        # We are interested in fields for plate_container and plate
        fields = {k:v for k,v in request.POST.items() if k.startswith('plate')}
 
        import pickle
        pickle.dump(dict(request.POST), open("/code/post.pkl", "wb"))

        # Submit a job to the server
        django_rq.enqueue(import_order_task, uuid=uuid, fields=fields)
        messages.info(request, "A task has been submit to the server to import this order.")
        return redirect('twist_order', uuid=uuid)

    return redirect('dashboard')


# Tasks

def import_order_task(uuid, fields):
    '''Based on an order id (uuid is the order sfdc_id in Twist)
       use FreeGenes Python to derive a list of plates (the PlateMap)
       and import plates and wells (physicals) into FreeGenes.

       Parameters
       ==========
       uuid: the order id, the sfdc_id from Twist
       fields: a lookup for plate_(id) and plate_container_(id), e.g.,

        {'plate_pSHPs0625B637913SH': ['name1'], 
         'plate_container_pSHPs0625B637913SH': ['05f2815e-7ff6-42d6-b42a-26d8273b133c'], 
         'plate_length_pSHPs0625B637913SH': ['12'], 
         'plate_height_pSHPs0625B637913SH': ['8'], 
         'plate_form_pSHPs0625B637913SH': ['standard96'],
        ...
        } 
    '''
    from fg.apps.main.models import Part
    from fg.apps.users.models import User
    from fg.apps.factory.twist import get_client
    
    print('RUNNING IMPORT ORDER TASK WITH UUID %s' % uuid)
    client = get_client()
    rows = client.order_platemaps(sfdc_id=uuid)
    print("Found %s total entries" % (len(rows) -1))

    # Separate header list 
    headers = rows.pop(0)

    # First create the plates - we need a lookup row for plate metadata
    plate_lookup = dict()
    for row in rows:
        plate_lookup[row[headers.index("Plate ID")]] = row
    
    plate_ids = list(plate_lookup.keys())
    plates = dict()

    for plate_id in plate_ids:

        container_id = fields.get("plate_container_%s" % plate_id)  
        plate_name = fields.get("plate_%s" % plate_id)
        plate_length = fields.get("plate_length_%s" % plate_id)
        plate_height = fields.get("plate_height_%s" % plate_id)
        plate_form = fields.get("plate_form_%s" % plate_id)
        product_type = plate_lookup[plate_id][headers.index("Product type")]

        # Create the plate if both exist
        if container_id and plate_name:

            container = Container.objects.get(uuid=container_id[0])
            try:
                plate = Plate.objects.get(plate_vendor_id=plate_id)

            # We want to create only if doesn't exist!
            except Plate.DoesNotExist:

                plate = None
                if product_type == "Clonal Genes":
                    plate = Plate.objects.create(name=plate_name[0],
                                                 container=container,
                                                 plate_vendor_id=plate_id,
                                                 plate_type="plasmid_plate",
                                                 plate_form=plate_form[0],
                                                 height=int(plate_height[0]),
                                                 length=int(plate_length[0]),
                                                 status="Stocked")

                elif product_type == "Glycerol stock":
                    plate = Plate.objects.create(name=plate_name[0],
                                                 container=container,
                                                 plate_vendor_id=plate_id,
                                                 plate_type="glycerol_stock",
                                                 plate_form=plate_form[0],
                                                 height=int(plate_height[0]),
                                                 length=int(plate_length[0]),
                                                 status="Stocked")

                # Save the object to lookup to add wells to
                if plate:
                    plates[plate.plate_vendor_id] = plate

    # We will only import wells for existing parts
    existing = Part.objects.filter(gene_id__in=names).values_list('gene_id', flat=True)
    
    # Now create the wells, add to their correct plate
    for row in rows:
        name = row[headers.index("Name")]

        # Only import existing parts
        if name in existing:
 
            product_type = plate_lookup[plate_id][headers.index("Product type")]
            plate_id = row[headers.index("Plate ID")]
            well_location = row[headers.index('Well Location')]
            plate = plates[plate_id]

            well = None
            if product_type == "Glycerol stock":
                well = Well.objects.create(address=well_location,
                                           volume=50,
                                           media="glycerol_lb")

            elif product_type == "Clonal genes"
                quantity = int(row[headers.index("Yield (ng)")])
                well = Well.objects.create(address=well_location,
                                           volume=0, # dried DNA
                                           quantity=quantity)

            if well:
                plate.wells.add(well)