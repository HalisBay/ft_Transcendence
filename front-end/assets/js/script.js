document.addEventListener('DOMContentLoaded', () => {
    // Tüm bağlantıları dinle
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); // Sayfanın yeniden yüklenmesini engelle
            const page = event.target.getAttribute('data-page');
            navigateTo(page); // İlgili sayfayı yükle
        });
    });

    // İlk yükleme sırasında uygun sayfayı yükle
    const initialPage = window.location.pathname.split('/')[1] || 'index';
    navigateTo(initialPage);

    // Kayıt Ol ve Giriş Yap butonları için dinleyici ekle
    document.addEventListener('DOMContentLoaded', () => {
        // Kayıt Ol butonunu dinle
        document.getElementById('go-to-register').addEventListener('click', () => {
            document.getElementById('login-container').style.display = 'none'; // Giriş Yap sayfasını gizle
            document.getElementById('register-container').style.display = 'block'; // Kayıt Ol sayfasını göster
        });

        // Giriş Yap butonunu dinle
        document.getElementById('go-to-login').addEventListener('click', () => {
            document.getElementById('register-container').style.display = 'none'; // Kayıt Ol sayfasını gizle
            document.getElementById('login-container').style.display = 'block'; // Giriş Yap sayfasını göster
        });
    });

    // Tarayıcıda geri/ileri tuşlarını yönet
    window.onpopstate = () => {
        const page = window.location.pathname.split('/')[1] || 'login';
        navigateTo(page, false); // Geçmişteki sayfayı yüklerken tarayıcı geçmişini güncelleme
    };
});

function navigateTo(page, updateHistory = true) {
    const app = document.getElementById('app');

    // İçeriği yükle
    fetch(`/static/pages/${page}.html`)
        .then(response => {
            if (!response.ok) throw new Error('Sayfa bulunamadı');
            return response.text();
        })
        .then(html => {
            app.innerHTML = html; // Yeni içeriği yükle

            // Yeni sayfa içeriğinde form varsa CSRF token'ını ekleyin
            const form = app.querySelector('form');
            if (form) {
                appendCSRFTokenToForm(form);
                form.addEventListener('submit', submitForm);
            }
        })
        .catch(error => {
            app.innerHTML = `<p class="text-danger">Hata: ${error.message}</p>`;
        });

    // Tarayıcı geçmişini güncelle (isteğe bağlı)
    if (updateHistory) {
        window.history.pushState({}, '', `/${page}`);
    }
}

function getCsrfToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    return tokenElement ? tokenElement.content : null;
}

function appendCSRFTokenToForm(form) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
        if (!form.querySelector('input[name="csrfmiddlewaretoken"]')) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
        }
    } else {
        console.error('CSRF token bulunamadı.');
    }
}

function submitForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const csrfToken = getCsrfToken();
    if (!csrfToken) {
        console.error("CSRF token bulunamadı!");
        return;
    }
    const formObject = {};
    formData.forEach((value, key) => {
        formObject[key] = value;
    });
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify(formObject)
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
    .catch(error => {
        console.error('Hata:', error);
    });
}
