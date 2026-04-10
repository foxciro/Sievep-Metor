let estado = 0;
$("form").submit((e) => {
  if ($("#submit").val() == "calcular") {
    estado = 1;
  }
});

const listeners_cambio = () => {
  $('input[type="number"]').keyup((e) => {
    if (estado === 1) {
      estado = 0;
      $("#submit").val("calcular");
      $("#submit").attr("name", "submit");
      $("#submit").html("Calcular Resultados");
      $("#resultados").html("");
    }
  });

  $("select").change((e) => {
    if (estado === 1) {
      estado = 0;
      $("#submit").val("calcular");
      $("#submit").attr("name", "submit");
      $("#submit").html("Calcular Resultados");
      $("#resultados").html("");
    }
  });
};

$("#id_presion_unidad").change((e) => {
  const array = $('select[name="presion_unidad"]').toArray().slice(1);

  array.map((x) => {
    x.innerHTML =
      "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
  });
});

$("#id_altura_unidad").change((e) => {
  const array = $('select[name="altura_unidad"]').toArray().slice(1);

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

$("#id_fluido, #id_calculo_propiedades").change((e) => {
  if (e.target.value === "A") {
    $("#id_viscosidad").attr("disabled", "disabled");
    $("#id_presion_vapor").attr("disabled", "disabled");
    $("#id_densidad").attr("disabled", "disabled");
  } else {
    $("#id_viscosidad").removeAttr("disabled");
    $("#id_presion_vapor").removeAttr("disabled");
    $("#id_densidad").removeAttr("disabled");

    if (e.target.value === "M") {
      $("#submit").removeAttr("disabled");
    }
  }

  if (e.target.value !== "F") {
    $("#id_viscosidad_unidad").removeAttr("disabled");
    $("#id_presion_vapor_unidad").removeAttr("disabled");
    $("#id_densidad_unidad").removeAttr("disabled");
    listeners_cambio();
  }
});

$("#id_calculo_propiedades").change((e) => {
  if (e.target.value !== "F") {
    $("#id_temperatura_operacion").removeAttr("disabled");
    $("#id_temperatura_unidad").removeAttr("disabled");
    $("#id_presion_unidad").removeAttr("disabled");
    $("#id_presion_succion").removeAttr("disabled");
    $("#id_presion_vapor_unidad").removeAttr("disabled");
    $("#id_viscosidad_unidad").removeAttr("disabled");
  }

  if (e.target.value == "M") $("button[type=submit]").removeAttr("disabled");
});

document.body.addEventListener("htmx:beforeRequest", function (evt) {
  const body = document.getElementsByTagName("body")[0];
  body.style.opacity = 0.25;

  if (
    evt.target.name === "form" &&
    Number($("#id_presion_succion").val()) >
      Number($("#id_presion_descarga").val())
  ) {
    evt.preventDefault();
    alert(
      "La presión de succión no puede ser mayor que la presión de la descarga. Verifique los datos."
    );
    body.style.opacity = 1.0;
    return;
  }

  if (document.getElementById("id_calculo_propiedades").value === "F") {
    if ($("#submit").val() === "almacenar") {
      evt.detail.xhr.target = document.getElementsByTagName("form")[0];
      if (!confirm("¿Está seguro que desea almacenar esta evaluación?")) {
        evt.preventDefault();
        body.style.opacity = 1.0;
      }
    }
    return;
  } else {
    $("#id_temperatura_operacion").removeAttr("disabled");
    $("#id_temperatura_unidad").removeAttr("disabled");
    $("#id_presion_unidad").removeAttr("disabled");
    $("#id_presion_succion").removeAttr("disabled");
    $("#id_presion_vapor_unidad").removeAttr("disabled");
    $("#id_viscosidad_unidad").removeAttr("disabled");
  }

  if (
    document.getElementById("id_calculo_propiedades").value == "M" ||
    document.getElementById("id_temperatura_operacion").value === "" ||
    document.getElementById("id_presion_succion").value === ""
  ) {
    if (evt.target.name !== "form") evt.preventDefault();

    if (document.getElementById("id_calculo_propiedades").value == "M") {
      $("#id_viscosidad").removeAttr("disabled");
      $("#id_presion_vapor").removeAttr("disabled");
      $("#id_densidad").removeAttr("disabled");
      $("#temperatura_operacion").removeAttr("disabled");
      $("#aviso").html("");
    }
    body.style.opacity = 1.0;
  }

  if (evt.target.name === "form") {
    if ($("#submit").val() === "almacenar") {
      evt.detail.xhr.target = document.getElementsByTagName("form")[0];
      if (!confirm("¿Está seguro que desea almacenar esta evaluación?")) {
        evt.preventDefault();
        body.style.opacity = 1.0;
      }
    } else {
      evt.detail.xhr.target = document.getElementById("resultados");
    }
  }
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
  if (
    evt.detail.failed ||
    $("#id_viscosidad").val() == "" ||
    $("#id_presion_vapor").val() == "" ||
    $("#id_densidad").val() == ""
  ) {
    alert(
      "Ha ocurrido un error al momento de obtener la información solicitada. Verifique que los datos están completos y son consistentes."
    );
    $("#id_viscosidad").val("");
    $("#id_presion_vapor").val("");
    $("#id_densidad").val("");
    $("#aviso").html("");
    document.body.style.opacity = 1.0;

    $("#submit").attr("disabled", "disabled");
  } else $("button[type=submit]").removeAttr("disabled");

  if (!evt.detail.failed && evt.target.name == "submit") {
    if ($("#submit").val() === "calcular" || $("#submit").val() === "") {
      $("#submit").val("almacenar");
    } else {
      $("#submit").val("calcular");
    }
  }

  listeners_cambio();
  $("#submit").attr("name", "submit");
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
  document.body.style.opacity = 1.0;
});

$('select[name="presion_unidad"]').html($('select[name="presion_unidad"]').html().replaceAll('</option>', 'g</option>'));

listeners_cambio();