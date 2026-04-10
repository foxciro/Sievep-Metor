$('.porc-vol').keyup(e => 
    $('#total-vol').val(
        $('.porc-vol').toArray().reduce((acc, el) => {
            return acc + Number(el.value);
        }, 0).toFixed(2)
    )
);

$('.porc-aire').keyup(e =>
    $('#total-aire').val(
        $('.porc-aire').toArray().reduce((acc, el) => {
            return acc + Number(el.value);
        }, 0).toFixed(2)
    )
);

const inicializarEventListeners = () => {
    $('#submit').click(e => {  
        // Verificar que la suma de ambos porcentajes correspondan al 100%
        const suma_volumen = $('.porc-vol').toArray().reduce((acc, el) => {
            return acc + Number(el.value);
        }, 0).toFixed(2);
    
        const suma_aire = $('.porc-aire').toArray().reduce((acc, el) => { 
            return acc + Number(el.value);
        }, 0).toFixed(2);
    
        if(suma_volumen != 100.00){
            e.preventDefault();
            alert("La suma de los porcentajes de volumen en la composición del combustible debe ser igual a 100.");
            return;
        }
    
        if(suma_aire != 100.00){
            e.preventDefault();
            alert("La suma de los porcentajes de aire en la composición del combustible debe ser igual a 100.");
            return;
        }

        if (!Array.from(document.querySelectorAll(`${$('#id_evaluacion-metodo').val() === 'D' ? '.directo-field' : '.indirecto-field'}`)).every(el => 
                 (el.name === 'superficie-area' || el.name === 'superficie-temperatura' || el.name === 'aire-velocidad') || el.value != ''
            )){
            e.preventDefault();
            alert("Todos los campos en verde deben ser llenados para poder realizar los cálculos correspondientes.");
            return;
        }
    
        if(!confirm("¿Está seguro que desea realizar esta acción?"))
            e.preventDefault();
    });

    $(".fase").change((e) => {
        const number = e.target.name
          .replaceAll("form", "")
          .replaceAll("-", "")
          .replaceAll(/[a-zA-Z]+/g, "");
            
        if ($(e.target).val() === "S") {    
          const presionInput = $(`input[name='form-${number}-presion']`);
          const temperaturaInput = $(`input[name='form-${number}-temperatura']`);
      
          presionInput.on('change', function() {
            if ($(this).val() !== "") {
              temperaturaInput.attr("disabled", "disabled");
            } else {
              temperaturaInput.removeAttr("disabled");
            }
          });
      
          temperaturaInput.on('change', function() {
            if ($(this).val() !== "") {
              presionInput.attr("disabled", "disabled");
            } else {
              presionInput.removeAttr("disabled");
            }
          });
        } else {
          $(`input[name='form-${number}-presion'], input[name='form-${number}-temperatura']`).removeAttr("disabled").off('input');
        }
      
        $(`input[name='form-${number}-presion'], input[name='form-${number}-temperatura']`).change();
      });
}

const inicializarResultados = () => {
    $('#resultados').html(`
        <div class="d-flex justify-content-center w-100">
            <button type="submit" id="submit" class="btn btn-danger w-full">Calcular Resultados</button>
        </div>`
    );
}

$('.form-control, .form-select').change(e => {
    inicializarResultados();
    inicializarEventListeners();
});

$('.form-control').keyup(e => {
    inicializarResultados();
    inicializarEventListeners();
});

$("#id_evaluacion-metodo").change(e => {
    if(e.target.value == 'D'){
        $(`.indirecto-field`).removeAttr('required');
        $(`.directo-field`).attr('required', 'required');
        $(`.indirecto-field`).css('border-color', '');
        $(`.directo-field`).css('border-color', 'green');
        $('#id_aire-humedad_relativa').val('').removeAttr('disabled');
    } else if(e.target.value == 'I'){
        $(`.directo-field`).removeAttr('required');
        $(`.indirecto-field`).attr('required', 'required'); 
        $(`.directo-field`).css('border-color', '');  
        $(`.indirecto-field`).css('border-color', 'green');

        $('#id_aire-humedad_relativa').val(2.4).attr('disabled', 'disabled');
    }

    $('#id_superficie-area').removeAttr('required');
    $('#id_superficie-temperatura').removeAttr('required');
    $('#id_aire-velocidad').removeAttr('required');
});

document.addEventListener("htmx:beforeRequest", function (evt) {
    document.body.style.opacity = 0.8;
  });

document.addEventListener("htmx:afterRequest", function (evt) {
  document.body.style.opacity = 1.0;
  inicializarEventListeners();

  if(evt.detail.failed)
    alert("Ha ocurrido un error al momento de realizar los cálculos. Por favor revise e intente de nuevo.");
});

$("#id_evaluacion-metodo").change();