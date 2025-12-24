from rest_framework.routers import DefaultRouter
from django.urls import path , include

from .views import(
    MeView  , AdminUsersView , EmailVerificationView
)

router = DefaultRouter()

router.register(r"admin/users",AdminUsersView,basename="admin-user")


urlpatterns = [
    path('me/', MeView.as_view,name="user-retrive-and-update-view"),
    path("verify-email/<uuid:token>/",EmailVerificationView.as_view(),name="email-verification"),
    path("", include(router.urls)),
]
