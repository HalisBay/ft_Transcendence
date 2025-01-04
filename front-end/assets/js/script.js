window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.split('/')[1] || 'home';
    navigateTo(initialPage);
});

function navigateTo(page) {
    const content = document.getElementById('content');

    // Yeni içeriği yükle
    fetch(`/${page}`)
        .then(response => {
            if (!response.ok) throw new Error(`Sayfa bulunamadı: ${response.status}`);
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;

            const newScripts = content.querySelectorAll('script');
            newScripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.defer = true;
                document.body.appendChild(newScript);
                script.remove();  // Eski scripti kaldır
            });

            // URL'yi güncelle
            const newUrl = `/${page}`;
            window.history.pushState({ page }, '', newUrl);
        })
        .catch(error => {
            content.innerHTML = `<p class="text-danger">Hata: ${error.message}</p>`;
        });
}

window.addEventListener('popstate', (event) => {
    const page = event.state?.page || 'home';
    navigateTo(page);
});

function submitForm(event) {
    event.preventDefault();  // Sayfa yenilemesini engelle

    const form = new FormData(event.target);  // Form verilerini al

    fetch('/register', {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
        },
    })
    .then(response => response.json())  // Yanıtı JSON formatında al
    .then(data => {
        if (data.success) {
            // Başarılı olursa kullanıcıyı login sayfasına yönlendir
            navigateTo('login');
        } else {
            //TODO: Burası hallolcak 
            document.getElementById('message').innerHTML = messageContent;  // messageContent kullan
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'Bir hata oluştu: ' + error.message;
    });
}

function submitFormOne(event) {
    event.preventDefault();  // Sayfa yenilemesini engelle

    const form = new FormData(event.target);  // Form verilerini al

    fetch('/login', {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
        },
    })
    .then(response => response.json())  // Yanıtı JSON formatında al
    .then(data => {
        console.log(JSON.stringify(data));
        if (data.success) {
            // JWT token'ı localStorage'a kaydediyoruz
            localStorage.setItem('access_token', data.access_token);

            // Başarılı olursa kullanıcıyı login sayfasına yönlendir
            navigateTo('verify');
        } else {
            localStorage.setItem('access_token', data.access_token);
            navigateTo('user');
            // Hata varsa, hata mesajını göster
            document.getElementById('message').innerHTML = data.message;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'Bir hata oluştu: ' + error.message;
    });
}

function activate2FA() {
    const csrfToken = getCsrfToken();
    fetch('/user/activate2fa', {  // URL burada 'user/activate-2fa/' olarak kaldı
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('2FA başarıyla etkinleştirildi!');
        }
    })
    .catch(error => {
        console.error('Hata oluştu:', error);
    });
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function toggleChatBoxes(targetBoxClass) {
    const chatBox = document.querySelector('.chat-box');
    const friendsBox = document.querySelector('.friends-box');
    const container = document.querySelector('.container');

    // Hedef kutu
    const currentBox = document.querySelector(`.${targetBoxClass}`);

    // Hedef kutu açılıyor ya da kapanıyor
    if (!currentBox.classList.contains('open')) {
        currentBox.classList.add('open');
        currentBox.classList.remove('close');
    } else {
        currentBox.classList.remove('open');
        currentBox.classList.add('close');
    }

    // Her iki kutunun durumunu kontrol et
    const isChatOpen = chatBox.classList.contains('open');
    const isFriendsOpen = friendsBox.classList.contains('open');

    // Container'ın pozisyonunu belirle
    if (isChatOpen && isFriendsOpen) {
        container.classList.add('shift-both');
        container.classList.remove('shift-chat', 'shift-friends');
    } else if (isChatOpen) {
        container.classList.add('shift-chat');
        container.classList.remove('shift-both', 'shift-friends');
    } else if (isFriendsOpen) {
        container.classList.add('shift-friends');
        container.classList.remove('shift-both', 'shift-chat');
    } else {
        // Kutuların hiçbiri açık değilse varsayılan duruma dön
        container.classList.remove('shift-both', 'shift-chat', 'shift-friends');
    }
}

function sendMessage(event) {
    // Formun varsayılan davranışını engelle (sayfa yenilenmesini önler)
    event.preventDefault();

    // Mesaj kutusundan girilen değeri al
    var message = document.getElementById("messageInput").value;

    // Eğer mesaj boş değilse, ekleme işlemi yap
    if (message.trim() !== "") {
        // Yeni bir div oluşturun ve mesajı ekleyin
        var messageDiv = document.createElement("div");
        messageDiv.classList.add("message"); // Mesaj kutusu sınıfını ekle
        messageDiv.textContent = message;

        // Mesajı #messages alanına ekleyin
        document.getElementById("messages").appendChild(messageDiv);

        // Mesaj kutusunu temizleyin
        document.getElementById("messageInput").value = "";

        // Mesajlar görünümünü en son mesaja kaydır
        var messagesContainer = document.getElementById("messages");
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    return false; // Form gönderimini tamamen engelle
}

// function getUserWithToken() {
//     const token = new URLSearchParams(window.location.search).get('token'); // URL'den token'ı al

//     if (!token) {
//         document.getElementById('message').innerHTML = 'Token bulunamadı.';
//         return;
//     }

//     fetch(`/verify?token=${token}`, {  // URL'ye token'ı ekle
//         method: 'GET',
//         headers: {
//             'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
//         },
//     })
//     .then(response => response.json())  // Yanıtı JSON formatında al
//     .then(data => {
//         console.log(JSON.stringify(data));
//         if (data.success) {
//             console.log('Token doğrulandı, kullanıcı sayfasına yönlendiriliyor...');
//             navigateTo('user');  // Yönlendirme yap
//         } else {
//             console.error('Token doğrulanamadı: ', data.message);
//             document.getElementById('message').innerHTML = data.message;
//         }
//     })
//     .catch(error => {
//         console.error('Bir hata oluştu: ', error.message);
//         document.getElementById('message').innerHTML = 'Bir hata oluştu: ' + error.message;
//     });
// }
