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