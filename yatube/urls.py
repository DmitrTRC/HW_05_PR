from django.contrib import admin
from django.urls import path, include
# from schema_graph.views import Schema
from django.conf.urls import handler404, handler500
from django.contrib.flatpages import views
from django.conf import settings
from django.conf.urls.static import static

handler404 = "posts.views.page_not_found"
handler500 = "posts.views.server_error"

urlpatterns = [
    # раздел администратора
    path("admin/", admin.site.urls),
    path("about/", include("django.contrib.flatpages.urls")),
    path("auth/", include("users.urls")),
    path("auth/", include("django.contrib.auth.urls")),

]

urlpatterns += [
    path('about-author/', views.flatpage,
         {'url': '/about-author/'}, name='about-author'),
    path('about-us/', views.flatpage, {'url': '/about-us/'}, name='about'),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'}, name='terms'),
    path('contacts/', views.flatpage,
         {'url': '/contacts/'}, name='pure_about'),
    path("", include("posts.urls")),

]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)

# urlpatterns += [
#     # On Django 2+:
#     path("demo/", Schema.as_view()),
#     # Or, on Django < 2:
#     url(r"^demo/$", Schema.as_view()),
# ]
