let socket = null; // Global bir WebSocket değişkeni tanımlayın
let pageHistory = [];

window.addEventListener('DOMContentLoaded', (event) => {
    const initialPage = window.location.pathname.substring(1) || 'home';
    navigateTo(initialPage);
});

// TODO: kullanıcı tarayıcıyı kapatınca olcak bu, bu düzeltilcek.
// window.onbeforeunload = function() {
//     fetch('/logout', {
//         method: 'POST',  // POST isteği yapılıyor
//         headers: {
//             'X-Requested-With': 'XMLHttpRequest',  // AJAX isteği olduğunu belirtiyoruz
//         },
//     })
//     document.cookie.split(';').forEach(function(c) {
//         document.cookie = c.trim().split('=')[0] + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
//     });
// };

function navigateTo(page) {
    const content = document.getElementById('content');

      // Aynı URL'yi tekrar eklememek için kontrol et
      if (pageHistory[pageHistory.length - 1] !== page) {
        pageHistory.push(page); // Yeni sayfayı geçmişe ekle
    }

    fetch(`/${page}`)
        .then(response => {
            if (!response.ok) throw new Error(`Page not found: ${response.status}`);
            return response.text();
        })
        .then(html => {
            content.innerHTML = html;
            updateButtonVisibility(page);

            const newScripts = content.querySelectorAll('script');
            newScripts.forEach(script => {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.defer = true;
                document.body.appendChild(newScript);
            });

            const newUrl = `/${page}`;
            window.history.pushState({ page }, '', newUrl);

            if (page === 'game/pong')
            {
                const gameMode = sessionStorage.getItem("game_mode") || "1v1";
                const alias = sessionStorage.getItem("player_alias");
                initiateWebSocketConnection(gameMode, alias);
            }
            else if (socket && socket.readyState === WebSocket.OPEN) {
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
    navigateTo(page);

window.addEventListener('beforeunload', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
     }
 });
});

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
    sessionStorage.setItem("game_mode", "1v1");
    navigateTo("game/pong");
}

function joinTournament(event) {
    event.preventDefault();
    const alias = document.getElementById("player-alias").value;
    if (!alias) {
        alert("Please fill in all fields!");
        return;
    }

    sessionStorage.setItem("game_mode", "tournament");
    sessionStorage.setItem("player_alias", alias);

    navigateTo("game/pong");
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

//let isTournamentCreated = false;
let isJoined = false;

// function waitingRoom(event) {
//     event.preventDefault();

//     if (isJoined || isTournamentCreated) {
//         document.getElementById('status').innerText = "Zaten bir turnuva oluşturdun knkm";
//         return;
//     }

//     const form = document.getElementById('create-tournament-form');
//     const creatorAlias = document.getElementById('creator-alias').value;
//     const tournamentName = document.getElementById('tournament-name').value;
    
//     socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

//     socket.onopen = function() {
//         socket.send(JSON.stringify({
//             'action': 'create_tournament',
//             'creator_alias': creatorAlias,
//             'tournament_name': tournamentName
//         }));
//     };

//     socket.onmessage = function(event) {
//         const data = JSON.parse(event.data);
//         if (data.error) {
//             document.getElementById('status').innerText = data.error;
//         } else {
//             document.getElementById('status').innerText = data.message;
//             isTournamentCreated = true;
//         }
//     };

//     socket.onclose = function(event) {
//         if (event.code === 1000) {
//             console.log("The connection was successfully closed.");
//         } else {
//             console.log("Connection closed:", event.code);
//         }
//         isTournamentCreated = false;
//     };

//     socket.onerror = function(event) {
//         document.getElementById('status').innerText = "Error: Unable to connect to the WebSocket.";
//     };
// }

// document.getElementById('startButton').addEventListener('click', function() {
//     console.log("Buton çalışıyor mu?")
//     checkOrStart();
// });

// let tourStarted = false;
// function checkOrStart() {
//     if (!socket || socket.readyState !== WebSocket.OPEN) {
//         // Eğer WebSocket bağlantısı açık değilse, kullanıcıya uyarı ver
//         document.getElementById('status').innerText = "Turnuvaya katılmadan oyunu başlatamazsınız!";
//         return;
//     }
//     socket.send(JSON.stringify({
//         'action': 'checkOrStart'
//     }));

//     socket.onmessage = function(e) {
//         const data = JSON.parse(e.data);
    
//         if (data.action === 'start_game') {
//             // When the game is ready to start, navigate to the pong page
//             navigateTo('game/pong');
//             tourStarted = true;
//         } else if (data.message) {
//             document.getElementById('status').innerText = data.message;
//         }
//     };
// }

// function leaveTournament() {
//     if (socket && socket.readyState === WebSocket.OPEN) {
//         socket.send(JSON.stringify({
//             'action': 'leave_tournament'
//         }));
//     } else {
//         console.error("WebSocket bağlantısı kapalı!");
//     }
// }


// function joinTournament(event) {
//     event.preventDefault();

//     const playerAlias = document.getElementById('player-alias').value; 
//     const tournamentName = document.getElementById('tournament-id').value; 

//     if (!playerAlias || !tournamentName) {
//         alert("Please fill in all fields!");
//         return;
//     }

//     if (isJoined) {
//         document.getElementById('status').innerText = "Zaten bir turnuvaya katıldın knkm";
//         return;
//     }

//     socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

//     socket.onopen = function() {
//         socket.send(JSON.stringify({
//             'action': 'join_tournament',
//             'player_alias': playerAlias,
//             'tournament_name': tournamentName
//         }));
//     };

//     socket.onmessage = function(event) {
//         const data = JSON.parse(event.data);

//         if (data.message) {
//             document.getElementById('status').innerText = data.message;
//         }

//         if (data.message.includes("O isimde Turnuva yokkk") || 
//             data.message.includes("Tournament not found") || 
//             data.message.includes("Could not add player") || 
//             data.message.includes("already a participant")) {
            
//             // Eğer katılım başarısızsa, bağlantıyı kapat
//             socket.close();
//         } else if (data.message.includes("joined the tournament")) {
//             isJoined = true;

//             const tournamentItem = document.querySelector(`#tournament-list li[data-tournament="${tournamentName}"]`);
//             if (tournamentItem) {
//                 tournamentItem.innerHTML += ' - Katıldın';
//             }
//         }
//     };

//     socket.onclose = function(event) {
//         console.log("WebSocket kapandı:", event.code);
//         isJoined = false;
//     };

//     socket.onerror = function(event) {
//         document.getElementById('status').innerText = "WebSocket bağlantı hatası!";
//     };
// }




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
        method: 'POST',
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
            method: 'POST',
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
        method: 'POST',
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



        if (message === "Password updated successfully, logging out.") {
            setTimeout(() => {
                navigateTo('login');
            }, 2000);
        }

    })
    .catch(error => {
        document.getElementById('message').innerHTML = `<p class="text-danger">An error occurred: ${error.message}</p>`;
    });
}



function submitAnonymizeForm(event) {
    event.preventDefault();  

    const form = new FormData(event.target); 

    fetch('/anonymize_account', {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  
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


setTimeout(function() {
    document.getElementById("message-container").style.display = "none";
}, 5000);



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



