function navigateTo(page) {
    const content = document.getElementById('content');

    // Eski içeriği fade-out yap
    content.classList.add('fade-out');

    // Fade-out tamamlandıktan sonra çalışacak bir dinleyici ekle
    content.addEventListener('animationend', function handleFadeOut() {
        content.removeEventListener('animationend', handleFadeOut); // Dinleyiciyi kaldır

        // Yeni içeriği yükle
        fetch(`${page}.html`)
            .then(response => {
                if (!response.ok) throw new Error('Sayfa bulunamadı');
                return response.text();
            })
            .then(html => {
                // İçeriği güncelle
                content.innerHTML = html;

                // Yeni içeriği fade-in yap
                content.classList.remove('fade-out');
                content.classList.add('fade-in');
            })
            .catch(error => {
                content.innerHTML = `<p class="text-danger">Hata: ${error.message}</p>`;
            });
    });
}

// Sayfa yüklendiğinde varsayılan sayfayı yükle
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('pages/home/home');
});




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

