let socket = null; // Global bir WebSocket değişkeni tanımlayın
let pageHistory = [];

window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.substring(1) || 'home';
    navigateTo(initialPage);
});

function navigateTo(page) {
    const content = document.getElementById('content');

      // Aynı URL'yi tekrar eklememek için kontrol et
      if (pageHistory[pageHistory.length - 1] !== page) {
        pageHistory.push(page); // Yeni sayfayı geçmişe ekle
    }

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
            });

            const newUrl = `/${page}`;
            window.history.pushState({ page }, '', newUrl);

            // WebSocket'i sadece belirli sayfada başlat
            if (page === 'game/pong')
                initiateWebSocketConnection();
            else if (socket && socket.readyState === WebSocket.OPEN) {
                socket.close(); // WebSocket'i diğer sayfalarda kapat
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
        console.log(JSON.stringify(data));  // Konsola da yazdırıyoruz (debug için)

        // 📝 Mesajı ekrana yazdır
        displayMessage(data.message, data.success);

        if (data.success) {
            localStorage.setItem('access_token', data.access_token);
            navigateTo('verify');
        } else {
            localStorage.setItem('access_token', data.access_token);
            navigateTo('user');
        }
    })
    .catch(error => {
        displayMessage('Bir hata oluştu: ' + error.message, false);
    });
}


function displayMessage(message, isSuccess) {
    const messageDiv = document.getElementById('message');

    // Mesajın görünür olmasını sağla
    messageDiv.style.display = 'block';
    messageDiv.innerText = message;

    // Başarı veya hata durumuna göre stil ver
    if (isSuccess) {
        messageDiv.style.color = 'green';
        messageDiv.style.backgroundColor = '#e6ffe6';
        messageDiv.style.border = '1px solid green';
    } else {
        messageDiv.style.color = 'red';
        messageDiv.style.backgroundColor = '#ffe6e6';
        messageDiv.style.border = '1px solid red';
    }
}



function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
function waitingRoom(event) {
    event.preventDefault();

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }

    socket = new WebSocket('ws://' + window.location.host + '/ws/tournament/');

    socket.onopen = () => {
      console.log('WebSocket bağlantısı başarıyla açıldı.');
      document.getElementById('status').innerHTML = 'Connecting...';
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'user_count_update') {
        document.getElementById('user-count').innerHTML = `Bağlı Kullanıcı Sayısı: ${data.user_count}`;
      } else if (data.type === 'start_tournament') {
        alert('Turnuva başlıyor!');
        // Oyunu başlatma işlemleri burada yapılabilir
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket hatası:', error);
    };

    socket.onclose = (event) => {
      console.log('WebSocket bağlantısı kapandı:', event);
    };

}

function initiateWebSocketConnection() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close(); // Eski bağlantıyı kapat
    }

    socket = new WebSocket('ws://' + window.location.host + '/ws/pong/');

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



function changeColors() {
    console.log("Button clicked");
    const switchElement = document.getElementById('colorSwitch'); // Doğru input elemanını seçiyoruz
    if (switchElement.checked) {
        console.log("Switch checked");
        document.getElementById('gameArea').style.backgroundColor = getRandomColor();
        document.getElementById('ball').style.backgroundColor = getRandomColor();
        document.getElementById('player1').style.backgroundColor = getRandomColor();
        document.getElementById('player2').style.backgroundColor = getRandomColor();
    } else {
        console.log("Switch unchecked");
        document.getElementById('gameArea').style.backgroundColor = '#000';
        document.getElementById('ball').style.backgroundColor = '#fff';
        document.getElementById('player1').style.backgroundColor = '#fff';
        document.getElementById('player2').style.backgroundColor = '#fff';
    }
}

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


function submitAnonymizeForm(event) {
    event.preventDefault();  // Sayfa yenilemesini engelle

    const form = new FormData(event.target);  // Form verilerini al

    fetch('/anonymize_account', {
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


function toggleFriendsPanel() {
    const panel = document.getElementById('friendsPanel');
    const body = document.body;

    if (panel.classList.contains('active')) {
        // Paneli kapat (fade-out ve kaydırma)
        panel.style.animation = 'fadeOut 0.3s'; // Fade-out animasyonu
        setTimeout(() => {
            panel.classList.remove('active'); // Paneli gizle
            body.classList.remove('shifted'); // Sayfayı eski haline getir
        }, 300); // Animasyon süresi kadar bekler
    } else {
        // Paneli aç (fade-in ve kaydırma)
        fetch('/friends/') // Arkadaş sayfanızın URL'si
            .then(response => response.text())
            .then(html => {
                panel.querySelector('.modal-content').innerHTML = html;
                panel.classList.add('active'); // Paneli göster
                panel.style.animation = 'fadeIn 0.3s'; // Fade-in efekti
                body.classList.add('shifted'); // Sayfayı sağa kaydır
            });
    }
}


function goBack() {
    if (pageHistory.length > 1) {
        pageHistory.pop(); // Son sayfayı diziden sil
        const previousPage = pageHistory[pageHistory.length - 1]; // Sonraki sayfayı al

        navigateTo(previousPage); // Geri gitmek için bu sayfayı yükle
    } else {
        // Eğer geçmişte başka sayfa yoksa, ilk sayfaya geri dön
        navigateTo('home')
    }
}



