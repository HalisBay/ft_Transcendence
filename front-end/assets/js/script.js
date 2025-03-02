let socket = null; // Global bir WebSocket değişkeni tanımlayın
let pageHistory = [];

window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.substring(1) || 'home';
    navigateTo(initialPage);
});

//TODO: kullanıcı tarayıcıyı kapatınca olcak bu, bu düzeltilcek.
window.onbeforeunload = function() {
    fetch('/logout', {
        method: 'POST',  // POST isteği yapılıyor
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
        },
    })
    document.cookie.split(';').forEach(function(c) {
        document.cookie = c.trim().split('=')[0] + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    });
};

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
        const messageElement = document.getElementById('message');
        if (data.success) {

            navigateTo('login');
        } else {
            // Hata mesajlarını göster
            let errorMessage = '';
            for (const [key, value] of Object.entries(data.errors)) {
                errorMessage += `<p class="text-danger">${value}</p>`;
            }
            messageElement.innerHTML = errorMessage;
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
        const messageElement = document.getElementById('message');
        console.log(JSON.stringify(data));
        if (data.success) {
            console.log(data.message)
            if (data.message.includes("2FA doğrulaması gerekiyor. Lütfen e-postanızı kontrol edin.")) {
                navigateTo('verify');
            } else {
                localStorage.setItem('access_token', data.access_token);
                
                navigateTo('user');
            }
        } else {
            // Hata mesajını göster
            let errorMessage = '';
            if (data.errors) {
                for (const [key, value] of Object.entries(data.errors)) {
                    errorMessage += `<p class="text-danger">${value}</p>`;
                }
            } else {
                errorMessage = `<p class="text-danger">${data.message}</p>`;
            }
            messageElement.innerHTML = errorMessage;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">Bir hata oluştu: ${error.message}</p>`;
    });
}
function logoutUser() {
    fetch('/logout', {
        method: 'POST',  // POST isteği yapılıyor
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
        },
    })
    .then(response => response.json())  // Yanıtı JSON formatında al
    .then(data => {
        const messageElement = document.getElementById('message');
        messageElement.innerHTML = `<p class="text-success">${data.message}</p>`;
        
        // Bir süre sonra kullanıcıyı login sayfasına yönlendir
        setTimeout(() => {
            navigateTo('login');
        }, 500);
    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">Bir hata oluştu: ${error.message}</p>`;
    });
}



function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
function waitingRoom(event) {
    event.preventDefault();

    const form = document.getElementById('create-tournament-form');
    const creatorAlias = document.getElementById('creator-alias').value;
    const tournamentName = document.getElementById('tournament-name').value;
    
    const socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

    socket.onopen = function() {
        // Once the connection is open, send the data
        socket.send(JSON.stringify({
            'action': 'create_tournament',
            'creator_alias': creatorAlias,
            'tournament_name': tournamentName
        }));
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.error) {
            document.getElementById('status').innerText = data.error;
        } else {
            document.getElementById('status').innerText = data.message;
        }
    };

    socket.onclose = function(event) {
        // Bağlantı kapandığında yapılacaklar
        if (event.code === 1000) {
            console.log("Bağlantı başarılı bir şekilde kapatıldı.");
        } else {
            console.log("Bağlantı kapatıldı:", event.code);
        }
    };

    socket.onerror = function(event) {
        document.getElementById('status').innerText = "Error: Unable to connect to the WebSocket.";
    };
}

function joinTournament(event) {
    event.preventDefault();

    const form = document.getElementById('join-tournament-form');
    const playerAlias = document.getElementById('player-alias').value; // Alias
    const tournamentName = document.getElementById('tournament-id').value; // Turnuva ismi (tournament name)

    // Eğer inputlardan biri null veya boşsa, form gönderilmesin
    if (!playerAlias || !tournamentName) {
        alert("Lütfen tüm alanları doldurun!");
        return;
    }

    const socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

    socket.onopen = function() {
        // Once the connection is open, send the data
        socket.send(JSON.stringify({
            'action': 'join_tournament',
            'player_alias': playerAlias,
            'tournament_name': tournamentName // Burada tournament-id yerine tournament-name kullanıyoruz
        }));
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.error) {
            document.getElementById('status').innerText = data.error;
        } else {
            document.getElementById('status').innerText = data.message;
            if (data.success && data.tournament_name === tournamentName) {
                // Katıldın bilgisini ilgili turnuvada anında göstermek
                const tournamentItem = document.querySelector(`#tournament-list li[data-tournament="${tournamentName}"]`);
                if (tournamentItem) {
                    tournamentItem.innerHTML += ' - Katıldın';
                }
            }
        }
        
        
        // Hata mesajı kontrolü
        if (data.message.includes("Could not add player") || data.message.includes("not found")) {
            alert(data.message);  // Kullanıcıya hata mesajını göster
            socket.close();       // ❗ Hata durumunda WebSocket bağlantısını kapat
        }
    };
    
    // Bağlantı kapatıldığında çalışacak kısım
    socket.onclose = function(event) {
        console.log("WebSocket bağlantısı kapatıldı:", event.code);
    };
    
    // Hata durumunda çalışacak kısım
    socket.onerror = function(error) {
        console.error("WebSocket hatası:", error);
        socket.close();  // ❗ Hata durumunda bağlantıyı kapat
    };
}



function initiateWebSocketConnection() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close(); // Eski bağlantıyı kapat
    }

    socket = new WebSocket('wss://' + window.location.host + '/ws/pong/');

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
    const messageDiv = document.getElementById("message");

    if (inputField.value.trim().toLowerCase() === "hesabımı sil") {
        deleteButton.disabled = false; // Butonu aktif hale getir
        messageDiv.textContent = "";  // Hata mesajını temizle
    } else {
        deleteButton.disabled = true; // Butonu devre dışı bırak
        messageDiv.textContent = "Lütfen 'hesabımı sil' yazın.";
        messageDiv.style.color = "red";
    }
}

document.getElementById("deleteForm").addEventListener("submit", function (event) {
    const inputField = document.getElementById("deleteInput");
    const messageDiv = document.getElementById("message");

    // Eğer input doğru değilse formu gönderme
    if (inputField.value.trim().toLowerCase() !== "hesabımı sil") {
        event.preventDefault();
        messageDiv.textContent = "Lütfen doğru metni girin: 'hesabımı sil'";
        messageDiv.style.color = "red";
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
        const messageElement = document.getElementById('message');
        messageElement.innerHTML = `<p class="text-success">${data.message}</p>`;

        if (data.message.includes("Şifre başarıyla güncellendi")) {
            // 2 saniye bekleyip login sayfasına yönlendir
            setTimeout(() => {
                navigateTo('login');
            }, 2000);
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">Bir hata oluştu: ${error.message}</p>`;
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


setTimeout(function() {
    document.getElementById("message-container").style.display = "none";
}, 5000);