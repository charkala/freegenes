'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
import fg.apps.orders.views as views

urlpatterns = [
    url(r'^$', views.orders_view, name='orders'),
    url(r'^cart/add/(?P<uuid>.+)$', views.add_to_cart, name='add-to-cart'),
    url(r'^cart/remove/(?P<uuid>.+)$', views.remove_from_cart, name='remove-from-cart'),
    url(r'^checkout$', login_required(views.CheckoutView.as_view()), name='checkout'),
    url(r'^checkout/(?P<uuid>.+)$', login_required(views.CheckoutView.as_view()), name='checkout'),
    url(r'^submit/(?P<uuid>.+)$', views.submit_order, name='submit_order'),

    # Material Transfer Agreement
    url(r'^mta/upload/(?P<uuid>.+)$', views.upload_mta, name='sign-mta'),
    url(r'^mta/admin-upload/(?P<uuid>.+)$', views.admin_upload_mta, name='upload-mta'),

    # Details (e corresponds for entity)
    url(r'^details/(?P<uuid>.+)$', views.order_details, name='order_details'),

    # Shipments
    url(r'^shipment/create/(?P<uuid>.+)$', login_required(views.ShippingView.as_view()), name='create_shipment'),
    url(r'^shipment/import-shippo-order$', login_required(views.ImportShippoView.as_view()), name='import_shippo_order'),
    url(r'^shipment/mark-shipped/(?P<uuid>.+)$', views.mark_as_shipped, name='mark_as_shipped'),
    url(r'^shipment/mark-received/(?P<uuid>.+)$', views.mark_as_received, name='mark_as_received'),
    url(r'^shipment/reject/(?P<uuid>.+)$', views.mark_as_rejected, name='mark_as_rejected'),
    url(r'^shipment/reset/(?P<uuid>.+)$', views.reset_shipment, name='reset_shipment'),
    url(r'^transaction/create/(?P<uuid>.+)$', views.create_transaction, name='create_transaction'),
    url(r'^transaction/tracking/update$', views.update_tracking, name='update_tracking'),
    url(r'^label/create/(?P<uuid>.+)$', views.create_label, name='create_label'),

]
