from django.urls import path
from . import views

urlpatterns = [
    path('', views.ManualOutboundListView.as_view(), name='outbound_list'),
    path('create/', views.ManualOutboundCreateView.as_view(), name='outbound_create'),
    path('<int:pk>/', views.ManualOutboundDetailView.as_view(), name='outbound_detail'),
    path('<int:pk>/update/', views.ManualOutboundUpdateView.as_view(), name='outbound_update'),
    path('<int:pk>/submit/', views.ManualOutboundSubmitView.as_view(), name='outbound_submit'),
    path('<int:pk>/delete/', views.ManualOutboundDeleteView.as_view(), name='outbound_delete'),
    path('<int:pk>/print/', views.ManualOutboundPrintView.as_view(), name='outbound_print'),
    path('<int:pk>/void/', views.ManualOutboundVoidView.as_view(), name='outbound_void'),
    path(
        '<int:order_pk>/close-item/<int:item_pk>/',
        views.ManualOutboundItemCloseView.as_view(),
        name='outbound_close_item',
    ),
    path('export/', views.ManualOutboundExportView.as_view(), name='outbound_export'),
    path('material-lookup/', views.MaterialLookupView.as_view(), name='material_lookup'),

    # User management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/password/', views.UserPasswordResetView.as_view(), name='user_password_reset'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='user_toggle_active'),

    # Reason management
    path('reasons/', views.ReasonListView.as_view(), name='reason_list'),
    path('reasons/create/', views.ReasonCreateView.as_view(), name='reason_create'),
    path('reasons/<int:pk>/update/', views.ReasonUpdateView.as_view(), name='reason_update'),
    path('reasons/<int:pk>/delete/', views.ReasonDeleteView.as_view(), name='reason_delete'),
]
