function handleTripChange(){
    const tripSelect = document.getElementById('tripSelect');
    const dateWrapper = document.getElementById('dateWrapper');

    if(tripSelect.value){
        dateWrapper.style.display = 'block';
        catWrapper.style.display = 'block';
    }else{
        dateWrapper.style.display = 'none';
        catWrapper.style.display = 'none';
    }

    tripSelect.form.submit();
}

document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll("input[name='payment_method']");

    radios.forEach(radio => {
        radio.addEventListener("click", function (e) {
            e.preventDefault();   // stop default radio behavior
            e.stopPropagation();

            const url = new URL(window.location.href);
            const current = url.searchParams.get("payment_method");
            const clicked = this.dataset.value;

            if (current === clicked) {
                // Unselect
                url.searchParams.delete("payment_method");
            } else {
                // Select
                url.searchParams.set("payment_method", clicked);
            }

            window.location.href = url.toString();
        });
    });
});
