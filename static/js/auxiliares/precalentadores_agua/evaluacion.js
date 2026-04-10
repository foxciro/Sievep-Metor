const cambio = () => {
  $("#resultados").html("");
  $(".change-blank").html("");
  $("#tipo_operacion").val("calcular");
}

$("form").keyup((e) => {
  cambio();    
});

$("form").change((e) => {
  cambio();    
});

document.body.addEventListener("htmx:beforeRequest", function (evt) {
    document.body.style.opacity = 0.8;
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
    document.body.style.opacity = 1;

    if(evt.detail.failed)
        alert("Ha ocurrido un error al momento de realizar los cálculos. Por favor revise e intente de nuevo.");
});

$('#submit').click(e => {
    const sum_flujos_entrada_carcasa = $('.flujo-entrada-carcasa').toArray().reduce((total, x) => total + Number(x.value), 0);
    const sum_flujos_salida_carcasa = $('.flujo-salida-carcasa').toArray().reduce((total, x) => total + Number(x.value), 0);
    
    if(sum_flujos_entrada_carcasa > 0 && sum_flujos_salida_carcasa > 0 &&
        sum_flujos_entrada_carcasa !== sum_flujos_salida_carcasa){
        e.preventDefault();
        alert("El flujo total de entrada de la carcasa debe ser igual al flujo total de salida.");
        return;
    }

    const sum_flujos_entrada_tubos = $('.flujo-entrada-tubos').toArray().reduce((total, x) => total + Number(x.value), 0);
    const sum_flujos_salida_tubos = $('.flujo-salida-tubos').toArray().reduce((total, x) => total + Number(x.value), 0);
    
    if(sum_flujos_entrada_tubos > 0 && sum_flujos_salida_tubos > 0 &&
        sum_flujos_entrada_tubos !== sum_flujos_salida_tubos){
        e.preventDefault();
        alert("El flujo total de entrada de los tubos debe ser igual al flujo total de salida.");
        return;
    }

    if(!confirm("¿Está seguro que desea realizar esta acción?"))
        e.preventDefault();
});

$("#id_flujo_unidad").change((e) => {
    const array = $('select[name="flujo_unidad"]').toArray().slice(1);
  
    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
  });

$("#id_temperatura_unidad").change((e) => {
    const array = $('select[name="temperatura_unidad"]').toArray().slice(1);
  
    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
});

$("#id_presion_unidad").change((e) => {
    const array = $('select[name="presion_unidad"]').toArray().slice(1);
  
    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
});

$("#id_entalpia_unidad").change((e) => {
    const array = $('select[name="entalpia_unidad"]').toArray().slice(1);
  
    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
});

$("#id_densidad_unidad").change((e) => {
    const array = $('select[name="densidad_unidad"]').toArray().slice(1);
  
    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
});