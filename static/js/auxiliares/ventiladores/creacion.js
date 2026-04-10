function anadir_listeners_dropboxes() {    
    $('#id_presion_unidad').change((e) => {
        const array = $('select[name="presion_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_adicional-presion_unidad').change((e) => {
        const array = $('select[name="adicional-presion_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_espesor_unidad').change((e) => {
        const array = $('select[name="espesor_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_potencia_freno_unidad').change((e) => {
        const array = $('select[name="potencia_freno_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_adicional-potencia_freno_unidad').change((e) => {
        const array = $('select[name="adicional-potencia_freno_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_temp_ambiente_unidad').change((e) => {
        const array = $('select[name="temp_ambiente_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_presion_barometrica_unidad').change((e) => {
        const array = $('select[name="presion_barometrica_unidad"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });

    $('#id_calculo_densidad').change((e) => {
        if(e.target.value === 'M')
            $('#id_densidad').removeAttr('disabled');
        else
            $('#id_densidad').attr('disabled', 'disabled');
    });

    $('#id_adicional-calculo_densidad').change((e) => {
        if(e.target.value === 'M')
            $('#id_adicional-densidad').removeAttr('disabled');
        else
            $('#id_adicional-densidad').attr('disabled', 'disabled');
    });
}

const anadir_listeners_htmx = () => {
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const body = document.getElementsByTagName('body')[0];
        body.style.opacity = 0.25;

        if(evt.target.id == 'id_complejo')
            return;
        
        if(evt.target.id.indexOf('adicional-') === -1) // Condiciones de Trabajo
            if(document.getElementById('id_calculo_densidad').value === 'M' || 
                document.getElementById('id_temperatura').value === '' && document.getElementById('id_temp_diseno').value === '' ||
                document.getElementById('id_presion_entrada').value === '' && document.getElementById('id_presion_diseno').value === '' 
            ){
                evt.preventDefault();
                if(document.getElementById('id_calculo_densidad').value === 'M'){
                    $('#id_densidad').removeAttr('disabled');
                    $('button[type=submit]').removeAttr('disabled');
                }
                    
                body.style.opacity = 1.0;
            }  else
                $('button[type=submit]').attr('disabled', 'disabled');
        else // Condiciones Adicionales
            if(document.getElementById('id_adicional-calculo_densidad').value === 'M' || 
            document.getElementById('id_adicional-temperatura').value === '' ||
            document.getElementById('id_adicional-presion_entrada').value === ''){
                evt.preventDefault();
                if(document.getElementById('id_adicional-calculo_densidad').value === 'M'){
                    $('#id_adicional-densidad').removeAttr('disabled');
                    $('button[type=submit]').removeAttr('disabled');                    
                }
                body.style.opacity = 1.0;
            }  else
                $('button[type=submit]').attr('disabled', 'disabled');            
    });

    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if(evt.detail.failed){
            alert("Ha ocurrido un error al momento de llevar a cabo los cálculos de la densidad del aire.");
            $('button[type=submit]').attr('disabled', 'disabled');

            if(evt.target.id.indexOf('adicional-') === -1)
                $('#id_densidad').val("");
            else
                $('#id_adicional-densidad').val("");
            document.body.style.opacity = 1.0;
        }
        else
            $('button[type=submit]').removeAttr('disabled');
    });
}

document.body.addEventListener('htmx:afterRequest', function(evt) {
    document.body.style.opacity = 1.0;
});

$('#submit').click(e => {
    if($('#id_presion_entrada').val() !== '' && $('#id_presion_salida').val() !== '' && Number($('#id_presion_entrada').val()) > Number($('#id_presion_salida').val())){
        alert("La presión de entrada debe ser menor o igual a la presión de salida (Condiciones de Trabajo).");
        e.preventDefault();
        return;
    }

    if($('#id_adicional-presion_entrada').val() !== '' && $('#id_adicional-presion_salida').val() !== '' && Number($('#id_adicional-presion_entrada').val()) > Number($('#id_adicional-presion_salida').val())){
        alert("La presión de entrada debe ser menor o igual a la presión de salida (Condiciones Adicionales).");
        e.preventDefault();
        return;
    } 

    if(!confirm("¿Está seguro que desea realizar esta acción?"))
        e.preventDefault();
})

$('form').submit(e => {
    $('#submit').attr('disabled','disabled');
})

anadir_listeners_htmx();
anadir_listeners_dropboxes();

$('#id_temperatura').change();
$('#id_adicional-temperatura').change();