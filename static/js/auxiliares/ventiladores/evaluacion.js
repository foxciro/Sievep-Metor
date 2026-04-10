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

$("#id_presion_salida_unidad").change((e) => {
  const array = $('select[name="presion_salida_unidad"]').toArray().slice(1);

  array.map((x) => {
    x.innerHTML =
      "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
  });
});

document.body.addEventListener("htmx:beforeRequest", function (evt) {
  const body = document.getElementsByTagName("body")[0];

  if (
    $("#id_presion_entrada").val() === "" ||
    $("#id_presion_salida").val() === "" ||
    $("#id_temperatura_operacion").val() === ""
  ) {
    $("#id_densidad_evaluacion").val("");
    evt.preventDefault();
    return;
  }

  if (
    $("#id_presion_entrada").val() !== "" &&
    $("#id_presion_salida").val() !== "" &&
    Number($("#id_presion_entrada").val()) >
      Number($("#id_presion_salida").val())
  ) {
    evt.preventDefault();
    alert(
      "La presión de entrada no puede ser mayor que la presión de salida. Verifique los datos."
    );
    $("#id_densidad_evaluacion").val("");
    $("#calcular").attr("disabled", "disabled");
    return;
  }

  if (evt.target.id === "form")
    if (!confirm("¿Seguro de que desea realizar esta acción?")) {
      evt.preventDefault();
      return;
    }

  body.style.opacity = 0.25;
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
  if (!evt.detail.failed) {
    $("#calcular").removeAttr("disabled");
  } else {
    alert(
      "Ocurrió un error al realizar los cálculos. Por favor intente de nuevo verificando la correctitud de los datos."
    );
    $("#id_densidad_evaluacion").val("");
    $("#calcular").attr("disabled", "disabled");
  }

  listeners_cambio();
});

document.body.addEventListener("htmx:afterRequest", function (evt) {
  document.body.style.opacity = 1.0;
});

$("input, select").change((e) => {
  $("#resultados").html(`
    <table class="table table-responsive table-bordered text-center">
        <tbody>
            <tr>
                <th colspan="2" class="table-dark w-50">
                    Resultados de la Evaluación
                </th>
            </tr>
            <tr>
                <th class="table-dark w-50">
                    Eficiencia de la Bomba
                </th>
                <td>
                </td>
            </tr>
            <tr>
                <th class="table-dark w-50">
                    Potencia Calculada
                </th>
                <td>
                </td>
            </tr>
        </tbody>
    </table>
`);
});

listeners_cambio();
