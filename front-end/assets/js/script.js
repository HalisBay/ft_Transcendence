window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.substring(1) || 'home';
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

            // WebSocket bağlantısını kontrol et veya başlat
            if (page === 'game/pong') {
                initiateWebSocketConnection();
            }
        })
        .catch(error => {
            content.innerHTML = `<p class="text-danger">Hata: ${error.message}</p>`;
        });
}


window.addEventListener('popstate', (event) => {
    const page = event.state?.page || 'home';
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
     }
    navigateTo(page);

window.addEventListener('beforeunload', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
     }
 });
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
            localStorage.setItem('refresh_token', data.refresh_token);

            // Başarılı olursa kullanıcıyı login sayfasına yönlendir
            navigateTo('verify');
        } else {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            navigateTo('user');
            // Hata varsa, hata mesajını göster
            document.getElementById('message').innerHTML = data.message;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'Bir hata oluştu: ' + error.message;
    });
}


function initiateWebSocketConnection() {
    const socket = new WebSocket('ws://' + window.location.host + '/ws/pong/');
    
    const statusElement = document.getElementById('status');

    socket.onopen = () => {
        console.log('WebSocket bağlantısı başarıyla açıldı.');
        statusElement.innerHTML = 'Connecting...';
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'game_message') {

            statusElement.innerHTML = data.message;
            if (data.scores) {
                statusElement.innerHTML += `<br>Score: ${data.scores.player1} - ${data.scores.player2}`;
            }
        } else if (data.type === 'game_state') {
            // Update status and score
            ball.style.left = data.state.ball.x + 'px';
            ball.style.top = data.state.ball.y + 'px';
            player1.style.top = data.state.players.player1.y + 'px';
            player2.style.top = data.state.players.player2.y + 'px';

            // If scores are present, update score display
            
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket hatası:', error);
    };

    socket.onclose = (event) => {
        console.log('WebSocket bağlantısı kapandı:', event);
    };

    // Handle player movement
    document.addEventListener('keydown', (e) => {
        if (e.key === 'w' || e.key === 'ArrowUp') {
            socket.send(JSON.stringify({ move: 'up' }));
        } else if (e.key === 's' || e.key === 'ArrowDown') {
            socket.send(JSON.stringify({ move: 'down' }));
        }
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
            alert('2FA Tercihi Güncellendi!');
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

function checkInput() {
        const inputField = document.getElementById("deleteInput");
        const deleteButton = document.getElementById("deleteButton");

        if (inputField.value.trim().toLowerCase() === "hesabımı sil") {
            deleteButton.disabled = false; // Butonu aktif hale getir
        } else {
            deleteButton.disabled = true; // Butonu devre dışı bırak
        }
    }


    document.getElementById("deleteForm").addEventListener("submit", function (event) {
        const inputField = document.getElementById("deleteInput");

        // Eğer input doğru değilse formu gönderme
        if (inputField.value.trim().toLowerCase() !== "hesabımı sil") {
            event.preventDefault();
            alert("Lütfen doğru metni girin: 'hesabımı sil'");
        }
    });
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



document.addEventListener('DOMContentLoaded', (event) => {
    console.log("Document loaded");
    const changeColorButton = document.getElementById('changeColorButton');
    changeColorButton.addEventListener('click', () => {
        console.log("Button clicked");
        const switchElement = document.getElementById('changeColorButton');
        if (switchElement.checked) {
            console.log("Switch checked");
            document.getElementById('gameArea').style.backgroundColor = '#000';
            document.getElementById('ball').style.backgroundColor = '#fff';
            document.getElementById('player1').style.backgroundColor = '#fff';
            document.getElementById('player2').style.backgroundColor = '#fff';
        } else {
            console.log("Switch unchecked");
            document.getElementById('gameArea').style.backgroundColor = getRandomColor();
            document.getElementById('ball').style.backgroundColor = getRandomColor();
            document.getElementById('player1').style.backgroundColor = getRandomColor();
            document.getElementById('player2').style.backgroundColor = getRandomColor();
        }
    });
});

function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}



function submitUpdatePasswordForm(event) {
    event.preventDefault();  // Sayfa yenilemesini engelle

    const form = new FormData(event.target);  // Form verilerini al

    fetch('/user/update_user', {
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
