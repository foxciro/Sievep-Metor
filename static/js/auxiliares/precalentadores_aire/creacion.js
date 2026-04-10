const anadir_listeners_dropboxes = (magnitud, prefix) => {
    const selector = prefix ? `select[name='${prefix}-${magnitud}_unidad']` : `select[name='${magnitud}_unidad']`
    $(selector).change((e) => {
        const array = $(selector).toArray().slice(1);
    
        array.map((x) => {
          x.innerHTML =
            "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });    
}

$("#submit").click((e) => {
    const suma_volumen = $('.porc-vol').toArray().reduce((acc, el) => {
        return acc + Number(el.value);
    }, 0).toFixed(2);

    const suma_aire = $('.porc-aire').toArray().reduce((acc, el) => { 
        return acc + Number(el.value);
    }, 0).toFixed(2);

    if(suma_volumen != 100.00){
        e.preventDefault();
        alert("La suma de los porcentajes de volumen en la composición de los gases debe ser igual a 100.");
        return;
    }

    if(suma_aire != 100.00){
        e.preventDefault();
        alert("La suma de los porcentajes de aire en la composición del aire debe ser igual a 100.");
        return;
    }
})

anadir_listeners_dropboxes('longitud', null);
anadir_listeners_dropboxes('area', null);

anadir_listeners_dropboxes('temp', 'aire');
anadir_listeners_dropboxes('presion', 'aire');

anadir_listeners_dropboxes('temp', 'gases');
anadir_listeners_dropboxes('presion', 'gases');

