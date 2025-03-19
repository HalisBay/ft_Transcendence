let socket = null;
let pageHistory = [];

window.addEventListener('DOMContentLoaded', () => {
    const initialPage = window.location.pathname.substring(1) || 'home';
    navigateTo(initialPage, false);
});

function navigateTo(page, addToHistory = true) {
    const content = document.getElementById('content');

    fetch(`/${page}`)
        .then(response => {
            if (!response.ok) throw new Error(`Page not found: ${response.status}`);
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;
            updateButtonVisibility(page);
            document.title = getPageTitle(page);

            if (addToHistory) {
                window.history.pushState({ page }, "", `/${page}`);
            } else {
                window.history.replaceState({ page }, "", `/${page}`);
            }

            if (page === 'home') {
                startAnimations(page); // Animasyonları başlat
            }

            if (page === 'game/pong') {
                const gameMode = sessionStorage.getItem("game_mode") || "1v1";
                const alias = sessionStorage.getItem("player_alias");
                initiateWebSocketConnection(gameMode, alias);
            } else if (socket && socket.readyState === WebSocket.OPEN) {
                socket.close();
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
    navigateTo(page, false);  // Geçmişe tekrar ekleme yapma
});

window.addEventListener('beforeunload', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }
});

function getPageTitle(page) {
    const titles = {
        "home": "Home",
        "about": "About",
        "game/home": "Game",
        "game/pong": "Pong",
        "register": "Register",
        "login": "Login",
        "activate_user": "Activate User",
        "verify": "Verify",
        "user": "User",
        "logout": "Logout",
        "notverified": "Not verified",
        "user/activate2fa": "User 2fa",
        "user/update": "Update",
        "user/update_user": "Update user",
        "user/delete": "Delete",
        "anonymize_account": "Anonymize Account",
        "gdpr": "GDPR",
        "game/tournament": "Tournament",
    };
    const profileMatch = page.match(/^game\/profile\/(\d+)$/);
    if (profileMatch) {
        const userId = profileMatch[1];
        return `Profile - ${userId}`;
    }
    return titles[page] || "Unknown Page";
}


function submitForm(event) {
    event.preventDefault(); 

    const form = new FormData(event.target);  

    fetch('/register', {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest', 
        },
    })
    .then(response => response.json()) 
    .then(data => {
        const messageElement = document.getElementById('message');
        if (data.success) {

            navigateTo('login');
        } else {
            let errorMessage = '';
            for (const [key, value] of Object.entries(data.errors)) {
                errorMessage += `<p class="text-danger">${value}</p>`;
            }
            messageElement.innerHTML = errorMessage;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'An error occurred: ' + error.message;
    });
}

function submitFormOne(event) {
    event.preventDefault();

    const form = new FormData(event.target); 

    fetch('/login', {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest', 
        },
    })
    .then(response => response.json())  
    .then(data => {
        const messageElement = document.getElementById('message');
        console.log(JSON.stringify(data));
        if (data.success) {
            console.log(data.message)
            if (data.message.includes("2FA verification required. Please check your email.")) {
                navigateTo('verify');
            } else {
                localStorage.setItem('access_token', data.access_token);
                
                navigateTo('user');
            }
        } else {
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
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}
function logoutUser() {
    fetch('/logout', {
        method: 'POST',  
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  
        },
    })
    .then(response => response.json())  
    .then(data => {
        const messageElement = document.getElementById('message');
        messageElement.innerHTML = `<p class="text-success">${data.message}</p>`;

        setTimeout(() => {
            navigateTo('login');
        }, 500);
    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}

function handleNextGame() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "next_game" }));
    }
    navigateTo('game/pong'); 
}

function leaveTournament() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "leave_tournament" }));
    }
    navigateTo('home');  // Oyuncuyu ana sayfaya yönlendir
}

function start1v1Game() {
    fetch("/game/home/check-active-game/")  // Sunucudan mevcut oyun durumunu kontrol et
        .then(response => response.json())
        .then(data => {
            const messageBox = document.getElementById("game-message"); // Mesaj göstermek için bir div seç
            if (data.in_game) {
                messageBox.innerHTML = "Zaten bir oyundasın!";
                messageBox.style.color = "red";  // Mesajı kırmızı yap (isteğe bağlı)
                messageBox.style.fontWeight = "bold";  // Kullanıcıya mesaj göster
            } else {
                sessionStorage.setItem("game_mode", "1v1");
                navigateTo("game/pong");  // Oyunda değilse yönlendirme yap
            }
        })
        .catch(error => {
            console.error("Oyun durumu kontrol edilirken hata oluştu:312312", error);
        });
}


function joinTournament(event) {
    event.preventDefault();
    const alias = document.getElementById("player-alias").value;
    const messageElement = document.getElementById("alias-message");

    if (!alias) {
        alert("Please fill in all fields!");
        return;
    }

    console.log("Checking active game...");
    
    fetch("/game/home/check-active-game/")
        .then(response => {
            console.log("Active game response status:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Active game response data:", data);
            if (data.in_game) {
                messageElement.innerHTML = `<p style="color: red;">Already in a game!</p>`;
                return null;  // ❗️ `null` dönerek zinciri kır
            }

            console.log("Checking alias availability...");
            return fetch("/game/tournament/check-alias/?alias=" + encodeURIComponent(alias));
        })
        .then(response => {
            if (!response) return; // ⬅️ Eğer `null` dönerse, devam etme!

            console.log("Alias check response status:", response.status);
            return response.json();
        })
        .then(data => {
            if (!data) return; // ⬅️ Eğer önceki adımda durduysak, devam etme!
            console.log("Alias check response data:", data);

            if (data.exists) {
                messageElement.innerHTML = `<p style="color: red;">This alias is already taken</p>`;
            } else {
                messageElement.innerHTML = "";
                sessionStorage.setItem("game_mode", "tournament");
                sessionStorage.setItem("player_alias", alias);
                navigateTo("game/pong");
            }
        })
        .catch(error => {
            console.error("Error in joinTournament:", error);
            alert("An error occurred. Please check the console for details.");
        });
}


function getCsrfToken() {
    const csrfElement = document.querySelector('meta[name="csrf-token"]') 
                      || document.querySelector('input[name="csrfmiddlewaretoken"]');
    return csrfElement ? csrfElement.getAttribute('content') || csrfElement.getAttribute('value') : null;
}


function initiateWebSocketConnection(gameMode, alias) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close(); 
    }

    let wsUrl = 'wss://' + window.location.host + '/ws/pong/';

    if (gameMode === "tournament") {
        wsUrl += `?tournament_mode=true&alias=${encodeURIComponent(alias)}`;
    } else {
        wsUrl += `?tournament_mode=false&alias=${encodeURIComponent(alias)}`;
    }


    socket = new WebSocket(wsUrl);

    const statusElement = document.getElementById('status');

    socket.onopen = () => {
        console.log('WebSocket connection opened successfully.');
        statusElement.innerHTML = 'Connecting...';
        socket.send(JSON.stringify({
            'action': 'getAlias',
            'alias': alias,

        }))
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "enable_next_game_button") {
            document.getElementById("nextGameBtn").disabled = false;
        }
        if (data.type === 'game_message') {
            statusElement.innerHTML = data.message;
            if (data.scores) {
                statusElement.innerHTML += `<br>Score: ${data.scores.player1} - ${data.scores.player2}`;
            }
        } else if (data.type === 'game_state') {
            ball.style.left = data.state.ball.x + 'px';
            ball.style.top = data.state.ball.y + 'px';
            player1.style.top = data.state.players.player1.y + 'px';
            player2.style.top = data.state.players.player2.y + 'px';
        }
        else if (data.type === "player_info") {
            document.getElementById("left-player").innerText = `Sol Oyuncu: ${data.left}`;
            document.getElementById("right-player").innerText = `Sağ Oyuncu: ${data.right}`;
        }
        
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
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
    const toggle = document.getElementById('toggle2FA');
    const isEnabled = toggle.checked;  // Açık/Kapalı durumunu kontrol et

    fetch('/user/activate2fa', {  
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ enable_2fa: isEnabled })  // Sunucuya durumu gönder
    })
    .then(response => response.json())
    .then(data => {
    })
    .catch(error => {
        console.error('Hata oluştu:', error);
        toggle.checked = !isEnabled; // Hata olursa geri al
    });
}



function deleteAccount() {
    const inputText = document.getElementById('inputText').value.trim().toLowerCase();
    const responseMessage = document.getElementById('responseMessage');
    
    if (inputText === "delete my account") {
        fetch('/user/delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ txt: inputText }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(JSON.stringify(data));
                const messageElement = document.getElementById('message');
                const message = data.success ? data.message : data.error_message;
                messageElement.className = data.success ? "text-success" : "text-danger";
                messageElement.innerHTML = `<p>${message}</p>`;
                setTimeout(() => {
                    navigateTo('register');
                }, 1000);
            } else {
                responseMessage.innerHTML = `<span style="color: red;">${data.message}</span>`;
            }
        })
        .catch(error => {
            responseMessage.innerHTML = `<span style="color: red;">Something went wrong. Please try again.</span>`;
        });
    } else {
        responseMessage.innerHTML = "<span style='color: red;'>Incorrect input. Please type 'delete my account'.</span>";
    }
}



function changeColors() {
    console.log("Button clicked");
    const switchElement = document.getElementById('colorSwitch'); 
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
    event.preventDefault(); 

    const form = new FormData(event.target);  

    fetch('/user/update_user', {
        method: 'PUT',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  
        },
    })
    .then(response => response.json())  
    .then(data => {
        console.log(JSON.stringify(data));
        const messageElement = document.getElementById('message');
        const message = data.success ? data.message : data.error_message;
        messageElement.className = data.success ? "text-success" : "text-danger";
        messageElement.innerHTML = `<p>${message}</p>`;



        if (message.includes("Password updated successfully, logging out.")) {
            setTimeout(() => {
                navigateTo('login');
            }, 1000);
        }

    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}



function submitAnonymizeForm(event) {
    event.preventDefault();  
    const csrfToken = getCsrfToken();
    const form = new FormData(event.target); 

    fetch('/anonymize_account', {
        method: 'PUT',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,  

        },
    })
    .then(response => response.json())  
    .then(data => {
        console.log(JSON.stringify(data));
        if (data.success) {
            navigateTo('user');
        } else {
            document.getElementById('message').innerHTML = data.message;
        }
    })
    .catch(error => {
        document.getElementById('message').innerHTML = 'An error occurred: ' + error.message;
    });
}


function toggleFriendsPanel() {
    const panel = document.getElementById('friendsPanel');
    const overlay = document.getElementById('overlay');

    if (panel.classList.contains('active')) {
        // Paneli kapat
        panel.style.animation = 'fadeOut 0.3s';
        overlay.classList.remove('active'); 
        setTimeout(() => {
            panel.classList.remove('active');
            panel.style.display = 'none';
            overlay.style.display = 'none';
        }, 300);
    } else {
        // Paneli aç
        fetch('/friends/')
            .then(response => response.text())
            .then(html => {
                panel.querySelector('.modal-content').innerHTML = html;
                panel.classList.add('active');
                panel.style.animation = 'fadeIn 0.3s';
                panel.style.display = 'block';
                overlay.classList.add('active');
                overlay.style.display = 'block';
            });
    }
}



function goBack() {
    if (pageHistory.length > 1) {
        pageHistory.pop();
        const previousPage = pageHistory[pageHistory.length - 1]; 

        navigateTo(previousPage);
    } else {
        navigateTo('home')
    }
}

function submitFriendsForm(event) {
    event.preventDefault();  
    const csrfToken = getCsrfToken();
    const form = event.target; 
    const url = form.getAttribute('action'); 
    const formData = new FormData(form);  

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest', 
            'X-CSRFToken': csrfToken,  
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const messageElement = document.getElementById('message');
        if (data.success) {
            setTimeout(() => {
                navigateTo('user');
            }, 500); 
            messageElement.innerHTML = `<p class="text-success">${data.message}</p>`;
        } else {
            messageElement.innerHTML = `<p class="text-danger">${data.message}</p>`;
        }
    })
    .catch(error => {
        console.error('Hata:', error);
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}


function handleFriendRequest(event, url) {
    event.preventDefault();  
    const csrfToken = getCsrfToken();

    fetch(url, {
        method: 'GET',  
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  
            'X-CSRFToken': csrfToken,  
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();  
    })
    .then(data => {
        const messageElement = document.getElementById('message');
        if (data.success) {
            messageElement.innerHTML = `<p class="text-success">${data.message}</p>`;
            navigateTo('user');
        } else {
            messageElement.innerHTML = `<p class="text-danger">${data.message}</p>`;
        }
    })
    .catch(error => {
        console.error('Hata:', error);
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}


function updateButtonVisibility(currentPage) {
    const gdprButton = document.querySelector(".GDPR");
    const aboutButton = document.querySelector(".GDPR2");
    const friendsButton = document.querySelector(".GDPR3");

    if (currentPage === "gdpr" || currentPage === "about") {
        gdprButton.style.display = "none"; 
        aboutButton.style.display = "none"; 
    } else {
        gdprButton.style.display = "block"; 
        aboutButton.style.display = "block";
    }
}

function startAnimations(page) {
    const transandece = document.getElementById('transandece');
    const contentt = document.getElementById('contentt');

    if (page === "home"){

        setTimeout(() => {
            transandece.style.transform = 'translate(-45%, -850%)';
        }, 250); 

        setTimeout(() => {
            contentt.style.opacity = '1';
        }, 600); // 3 saniye sonra içeriği görünür yap
    }
}

// Sayfa yüklendiğinde animasyonları başlat
window.onload = startAnimations;