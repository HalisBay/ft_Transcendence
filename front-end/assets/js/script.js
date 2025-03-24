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

            setTimeout(() => {
                if (page === 'game/pong') {
                    const gameMode = sessionStorage.getItem("game_mode") || "1v1";
                    const alias = sessionStorage.getItem("player_alias");
                    if (gameMode === "local") { // Local modu başlat
                        startLocalPongGame();
                    } else {
                        isLocalMode = false;
                        initiateWebSocketConnection(gameMode, alias);
                    }
                    console.log("isLocalMode:", isLocalMode);
                } else if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.close();
                }
            }, 100);
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
    navigateTo('user');  // Oyuncuyu ana sayfaya yönlendir
}

function start1v1Game() {
    fetch("/game/home/check-active-game/")  // Sunucudan mevcut oyun durumunu kontrol et
        .then(response => response.json())
        .then(data => {
            const messageBox = document.getElementById("game-message"); // Mesaj göstermek için bir div seç
            if (data.in_game) {
                messageBox.innerHTML = "You're already in a game.";
                messageBox.style.color = "red";  // Mesajı kırmızı yap (isteğe bağlı)
                messageBox.style.fontWeight = "bold";  // Kullanıcıya mesaj göster
            } else {
                sessionStorage.setItem("game_mode", "1v1");
                navigateTo("game/pong");  // Oyunda değilse yönlendirme yap
            }
        })
        .catch(error => {
            console.error("An error occurred while checking the game state:", error);
        });
}

function startLocalGame() {
    sessionStorage.setItem("game_mode", "local");  // Local modda oynandığını sakla
    navigateTo("game/pong"); // Oyunun oynandığı sayfaya git
}


const GAME_WIDTH = 1000;
const GAME_HEIGHT = 580;
const BALL_SIZE = 13;
const BALL_RADIUS = BALL_SIZE / 2;
const PADDLE_WIDTH = 5;
const PADDLE_HEIGHT = 60;
const PADDLE_SPEED = 18;
const WINNING_SCORE = 2;

let isLocalMode = false;
let gameActive = false;

// **Local Pong Değişkenleri**
let scoresL, ballL, playersL;

// **Local Pong Başlatma**
function startLocalPongGame() {
    isLocalMode = true;
    gameActive = true;
    scoresL = { player1: 0, player2: 0 };
    ballL = { x: 500, y: 290, vx: 1.0, vy: 1.0 };
    playersL = { player1: { y: 260 }, player2: { y: 260 } };

    document.getElementById("left-player").innerText = "Left Player: WASD - Player 1";
    document.getElementById("right-player").innerText = "Right Player: arrow keys - Player 2";
    document.getElementById("status").innerText = "Game Started!";

    // Local event dinleyicileri ekle
    document.addEventListener("keydown", handleLocalKeydown);
    startLocalGameLoop();
}

// **Local Pong Oyun Döngüsü**
function startLocalGameLoop() {
    if (!isLocalMode) return;

    function gameLoop() {
        if (!gameActive) return;

        moveBall();
        updateGameView();
        setTimeout(gameLoop, 50);
    }

    gameLoop();
}

// **Local Pong Top Hareketi**
function moveBall() {
    if (!gameActive || !isLocalMode) return;

    ballL.x += ballL.vx * 10;
    ballL.y += ballL.vy * 10;

    if (ballL.y - BALL_RADIUS <= 0 || ballL.y + BALL_RADIUS >= GAME_HEIGHT) {
        ballL.vy = -ballL.vy;
    }

    // **Sol paddle çarpışma kontrolü**
    if (
        ballL.x - BALL_RADIUS <= PADDLE_WIDTH &&
        ballL.y >= playersL.player1.y &&
        ballL.y <= playersL.player1.y + PADDLE_HEIGHT
    ) {
        ballL.vx = -ballL.vx;
        ballL.x = PADDLE_WIDTH + BALL_RADIUS;
    }
    // **Sağ paddle çarpışma kontrolü**
    else if (
        ballL.x + BALL_RADIUS >= GAME_WIDTH - PADDLE_WIDTH &&
        ballL.y >= playersL.player2.y &&
        ballL.y <= playersL.player2.y + PADDLE_HEIGHT
    ) {
        ballL.vx = -ballL.vx;
        ballL.x = GAME_WIDTH - PADDLE_WIDTH - BALL_RADIUS;
    }

    // **Gol kontrolü**
    if (ballL.x - BALL_RADIUS <= 0) {
        scoresL.player2++;
        updateScore();
        checkGameEnd();
        resetBall(1);
    } else if (ballL.x + BALL_RADIUS >= GAME_WIDTH) {
        scoresL.player1++;
        updateScore();
        checkGameEnd();
        resetBall(-1);
    }
}

// **Topu başlangıç konumuna döndür**
function resetBall(directionL) {
    ballL = { 
        x: 500.0, 
        y: 290.0, 
        vx: directionL * 1.0, 
        vy: (Math.random() > 0.5 ? 1.0 : -1.0) // %50 yukarı, %50 aşağı gitmesi için
    };
}

// **Paddle hareket ettirme**
function movePaddle(player, directionL) {
    if (!gameActive) return;

    if (player === "player1") {
        if (directionL === "up") {
            playersL.player1.y = Math.max(0, playersL.player1.y - PADDLE_SPEED);
        } else if (directionL === "down") {
            playersL.player1.y = Math.min(GAME_HEIGHT - PADDLE_HEIGHT, playersL.player1.y + PADDLE_SPEED);
        }
    } else if (player === "player2") {
        if (directionL === "up") {
            playersL.player2.y = Math.max(0, playersL.player2.y - PADDLE_SPEED);
        } else if (directionL === "down") {
            playersL.player2.y = Math.min(GAME_HEIGHT - PADDLE_HEIGHT, playersL.player2.y + PADDLE_SPEED);
        }
    }
}

// **Skoru güncelle**
function updateScore() {
    document.getElementById("status").innerText = `Score: ${scoresL.player1} - ${scoresL.player2}`;
}

// **Oyunu bitirme kontrolü**
function checkGameEnd() {
    if (scoresL.player1 >= WINNING_SCORE) {
        endGame("Player 1 Winner!");
        document.getElementById("nextGameBtn").disabled = false;
    } else if (scoresL.player2 >= WINNING_SCORE) {
        endGame("Player 2 Winner!");
        document.getElementById("nextGameBtn").disabled = false;
    }
}

// **Oyun bittiğinde mesaj göster**
function endGame(message) {
    gameActive = false;
    document.getElementById("status").innerText = message;
    document.removeEventListener("keydown", handleLocalKeydown); 
}

// **HTML içindeki paddle ve top konumlarını güncelle**
function updateGameView() {
        document.getElementById("ball").style.left = `${ballL.x}px`;
        document.getElementById("ball").style.top = `${ballL.y}px`;
        document.getElementById("player1").style.top = `${playersL.player1.y}px`;
        document.getElementById("player2").style.top = `${playersL.player2.y}px`;
}
// **Local Pong Paddle Hareket Ettirme**
function handleLocalKeydown(event) {
    if (!isLocalMode) return;

    if (event.key === "w") movePaddle("player1", "up");
    if (event.key === "s") movePaddle("player1", "down");
    if (event.key === "ArrowUp") movePaddle("player2", "up");
    if (event.key === "ArrowDown") movePaddle("player2", "down");
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
            if (!data.state.players || !data.state.players.player1 || !data.state.players.player2) {
                return;
            }
            ball.style.left = data.state.ball.x + 'px';
            ball.style.top = data.state.ball.y + 'px';
            player1.style.top = data.state.players.player1.y + 'px';
            player2.style.top = data.state.players.player2.y + 'px';
        }
        else if (data.type === "player_info") {
            document.getElementById("left-player").innerText = `Left Player: ${data.left}`;
            document.getElementById("right-player").innerText = `Right Player: ${data.right}`;
        }
        
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
    };
 // Hareket intervali
    addWebSocketEventListeners();
  
}

let movementInterval = null;

function handleWebSocketKeydown(e) {
    if (isLocalMode || e.repeat || movementInterval) return;

    let direction = null;
    if (e.key === "w" || e.key === "ArrowUp") direction = "up";
    else if (e.key === "s" || e.key === "ArrowDown") direction = "down";

    if (direction) {
        socket.send(JSON.stringify({ type: "move", direction }));
        movementInterval = setInterval(() => {
            socket.send(JSON.stringify({ type: "move", direction }));
        }, 20);
    }
}

// WebSocket için keyup event handler
function handleWebSocketKeyup(e) {
    if (isLocalMode) return;

    if (["w", "ArrowUp", "s", "ArrowDown"].includes(e.key)) {
        socket.send(JSON.stringify({ type: "move", direction: "stop" }));
        clearInterval(movementInterval);
        movementInterval = null;
    }
}

function addWebSocketEventListeners() {
    document.addEventListener("keydown", handleWebSocketKeydown);
    document.addEventListener("keyup", handleWebSocketKeyup);
}

// Event listener'ları kaldıran fonksiyon
function removeWebSocketEventListeners() {
    document.removeEventListener("keydown", handleWebSocketKeydown);
    document.removeEventListener("keyup", handleWebSocketKeyup);
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