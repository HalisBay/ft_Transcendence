function navigateTo(page) {
    const content = document.getElementById('content');

    // Yeni içeriği yükle
    fetch(`${page}`)
        .then(response => {
            if (!response.ok) throw new Error('Sayfa bulunamadı');
            return response.text();
        })
        .then(html => {
            // İçeriği güncelle
            content.innerHTML = html;

            // URL'yi güncelle
            const newUrl = `/${page}`;
            window.history.pushState({ page }, '', newUrl);
        })
        .catch(error => {
            content.innerHTML = `<p class="text-danger">Hata: ${error.message}</p>`;
        });
}

// İlk yüklemede doğru sayfayı belirle
const initialPage = window.location.pathname.split('/')[1] || 'home';
navigateTo(initialPage);

// Geri veya ileri düğmelerine basıldığında sayfayı yükle
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
