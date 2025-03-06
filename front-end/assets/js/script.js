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
                initiateWebSocketConnection();
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



function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
function waitingRoom(event) {
    event.preventDefault();

    const form = document.getElementById('create-tournament-form');
    const creatorAlias = document.getElementById('creator-alias').value;
    const tournamentName = document.getElementById('tournament-name').value;
    
    socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

    socket.onopen = function() {
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
        if (event.code === 1000) {
            console.log("The connection was successfully closed.");
        } else {
            console.log("Connection closed:", event.code);
        }
    };

    socket.onerror = function(event) {
        document.getElementById('status').innerText = "Error: Unable to connect to the WebSocket.";
    };
}

function joinTournament(event) {
    event.preventDefault();

    const form = document.getElementById('join-tournament-form');
    const playerAlias = document.getElementById('player-alias').value; 
    const tournamentName = document.getElementById('tournament-id').value; 

    if (!playerAlias || !tournamentName) {
        alert("Please fill in all fields!");
        return;
    }

    socket = new WebSocket('wss://' + window.location.host + '/ws/tournament/');

    socket.onopen = function() {
        socket.send(JSON.stringify({
            'action': 'join_tournament',
            'player_alias': playerAlias,
            'tournament_name': tournamentName
        }));
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.error) {
            document.getElementById('status').innerText = data.error;
        } else {
            document.getElementById('status').innerText = data.message;
            if (data.success && data.tournament_name === tournamentName) {
                const tournamentItem = document.querySelector(`#tournament-list li[data-tournament="${tournamentName}"]`);
                if (tournamentItem) {
                    tournamentItem.innerHTML += ' - Katıldın';
                }
            }
        }
        
        
        if (data.message.includes("Could not add player") || data.message.includes("not found")) {
            alert(data.message);  
            socket.close();      
        }
    };
    

    socket.onclose = function(event) {
        console.log("WebSocket connection closed:", event.code);
    };
    
    // Hata durumunda çalışacak kısım
    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
        socket.close();  
    };
}



function initiateWebSocketConnection() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close(); 
    }

    socket = new WebSocket('wss://' + window.location.host + '/ws/pong/');

    const statusElement = document.getElementById('status');

    socket.onopen = () => {
        console.log('WebSocket connection opened successfully.');
        statusElement.innerHTML = 'Connecting...';
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
    fetch('/user/activate2fa', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('2FA Preference Updated!');
        }
    })
    .catch(error => {
        console.error('Error occurred:', error);
    });
}



function checkInput() {
    const inputField = document.getElementById("deleteInput");
    const deleteButton = document.getElementById("deleteButton");
    const messageDiv = document.getElementById("message");
    
    if (inputField.value.trim().toLowerCase() === "delete my account") {
        deleteButton.disabled = false; 
        messageDiv.textContent = "";  

        fetch('/user/delete', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                navigateTo('user');
            } else {
                messageDiv.textContent = "Error: " + data.message || "An error occurred.";
                messageDiv.style.color = "red";
            }
        })
        .catch(error => {
            console.error('Error occurred:', error);
            messageDiv.textContent = "An error occurred. Please try again.";
            messageDiv.style.color = "red";
        });
    } else {
        deleteButton.disabled = true; 
        messageDiv.textContent = "Please type 'delete my account'.";
        messageDiv.style.color = "red";
    }
}


function delemOne(event) {
    event.preventDefault();

    const form = new FormData(event.target); 

    fetch('/user/delete', {
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
            navigateTo('home')
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
//         console.error('An error occurred: ', error.message);
//         document.getElementById('message').innerHTML = 'An error occurred: ' + error.message;
//     });
// }



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