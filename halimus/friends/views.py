from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from transcendence.requireds import jwt_required,notlogin_required
from django.contrib.auth.decorators import login_required
from .models import User,FriendList, FriendRequest
from django.db.models import Case, When, IntegerField
from django.db import models




@login_required
def friend_list(request):
    """Arkadaş listesi ve istekleri görüntüleme"""
    friend_list = FriendList.objects.filter(user=request.user).first()
    received_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
    sent_requests = FriendRequest.objects.filter(from_user=request.user, status='pending')

    # Arkadaş listesini online kullanıcılar üstte olacak şekilde sırala
    if friend_list:
        sorted_friends = friend_list.friends.annotate(
            is_online_order=Case(
                When(is_online=True, then=0),  # Online kullanıcılar önce
                default=1,  # Çevrimdışı kullanıcılar sonra
                output_field=models.IntegerField(),
            )
        ).order_by('is_online_order', 'nick')  # İkincil olarak alfabetik sıralama
    else:
        sorted_friends = None

    context = {
        'friend_list': friend_list,
        'sorted_friends': sorted_friends,  # Sıralanmış arkadaşlar
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }

    return render(request, 'pages/friend_list.html', context)


@login_required
def send_friend_request(request):
    """Arkadaşlık isteği gönderme"""
    if request.method == 'POST':
        nick = request.POST.get('nick')
        if not nick:
            messages.error(request, "Kullanıcı adı girilmelidir.")
            return redirect('user')

        try:
            to_user = User.objects.get(nick=nick)  # Kullanıcıyı nick ile arıyoruz
            if to_user == request.user:
                messages.error(request, "Kendinize istek gönderemezsiniz.")
            else:
                # Arkadaşlık kontrolü
                friend_list, created = FriendList.objects.get_or_create(user=request.user)
                if friend_list.is_friend(to_user):
                    messages.info(request, "Bu kullanıcı zaten arkadaşınız.")
                    return redirect('user')

                # Aynı isteği daha önce göndermiş mi kontrol ediyoruz
                existing_request = FriendRequest.objects.filter(from_user=request.user, to_user=to_user, status='pending').exists()
                if existing_request:
                    messages.info(request, "Bu kullanıcıya zaten istek gönderdiniz.")
                else:
                    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
                    messages.success(request, f"{nick} adlı kullanıcıya arkadaşlık isteği gönderildi.")
        except User.DoesNotExist:
            messages.error(request, "Kullanıcı bulunamadı.")
        return redirect('user')


@login_required
def accept_friend_request(request, request_id):
    """Arkadaşlık isteğini kabul et"""
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.accept()
    return redirect('user')

@login_required
def reject_friend_request(request, request_id):
    """Arkadaşlık isteğini reddet"""
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.reject()
    return redirect('user')
