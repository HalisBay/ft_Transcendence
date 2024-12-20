window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.split('/')[1] || 'home';
    navigateTo(initialPage);
});

// window.onbeforeunload = function(event) {
//     event.preventDefault();
//   };

  function navigateTo(page) {
    const content = document.getElementById('content');
    console.log(content);

    // Yeni içeriği yükle
    fetch(`/${page}`)
        .then(response => {
            console.log('Gelen Yanıt Durumu:', response.status);
            if (!response.ok) throw new Error(`Sayfa bulunamadı: ${response.status}`);
            return response.text();
        })
        .then(html => {
            console.log(`Yeni içerik yüklendi: ${page}`);
            content.innerHTML = html;

            // Sayfa yüklenince JavaScript dosyalarını yeniden yükle
            const scripts = content.querySelectorAll('script');
            scripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.onload = () => console.log(`Script yüklendi: ${script.src}`);
                document.body.appendChild(newScript);
            });

            // URL'yi güncelle
            const newUrl = `/${page}`;
            window.history.pushState({ page }, '', newUrl);
        })
        .catch(error => {
            console.error('Fetch hatası:', JSON.stringify(error));
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
            // Hata varsa, hata mesajını göster
            document.getElementById('message').innerHTML = data.message;
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
            // Başarılı olursa kullanıcıyı login sayfasına yönlendir
            navigateTo('user');
        } else {
            // Hata varsa, hata mesajını göster
            document.getElementById('message').innerHTML = data.message;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'Bir hata oluştu: ' + error.message;
    });
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