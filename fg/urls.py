'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from importlib import import_module

from django.conf import settings
from django.conf.urls import (include, url)
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap, index
from fg.apps.api import urls as api_urls
from fg.apps.base import urls as base_urls
from fg.apps.main import urls as main_urls
from fg.apps.orders import urls as orders_urls
from fg.apps.factory import urls as factory_urls
from fg.apps.users import urls as user_urls
from django.contrib import admin
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls

# Customize admin title, headers
admin.site.site_header = 'FreeGenes administration'
admin.site.site_title = 'FreeGenes Admin'
admin.site.index_title = 'FreeGenes administration'

# Documentation URL
API_TITLE = 'FreeGenes API'
API_DESCRIPTION = 'FreeGenes Resource API'
schema_view = get_schema_view(title=API_TITLE)

# Configure custom error pages
handler404 = 'fg.apps.base.views.handler404'
handler500 = 'fg.apps.base.views.handler500'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include(base_urls)),
    url(r'^api/', include(api_urls)),
    url(r'^api/schema/$', schema_view, name='api-schema'),
    url(r'^api/docs/', include_docs_urls(title=API_TITLE, description=API_DESCRIPTION)),
    url(r'^o/', include(orders_urls)),
    url(r'^f/', include(factory_urls)),
    url(r'^', include(main_urls)),
    url(r'^', include(user_urls)),
    url(r'^django-rq/', include('django_rq.urls'))
]

# Load URLs for any enabled plugins
for plugin in settings.PLUGINS_ENABLED:
    urls_module = 'fg.plugins.' + plugin + '.urls'
    plugin_urls = import_module(urls_module)
    url_regex = '^' + plugin + '/'
    urlpatterns.append(url(url_regex, include(plugin_urls)))
