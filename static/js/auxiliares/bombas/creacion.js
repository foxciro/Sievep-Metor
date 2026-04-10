function anadir_listeners_dropboxes() {
  $("#id_id_unidad").change((e) => {
    const array = $('select[name="id_unidad"]').toArray().slice(1);

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

  $("#id_temperatura_unidad").change((e) => {
    const array = $('select[name="temperatura_unidad"]').toArray().slice(1);

    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
  });

  $("#id_concentracion_unidad").change((e) => {
    const array = $('select[name="concentracion_unidad"]').toArray().slice(1);

    array.map((x) => {
      x.innerHTML =
        "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
    });
  });

  $("#id_tipo_carcasa1").change((e) => {
    if (e.target.value) $("#id_tipo_carcasa2").removeAttr("disabled");
    else $("#id_tipo_carcasa2").attr("disabled", "disabled");
  });

  $("#id_fluido, #id_calculo_propiedades").change((e) => {
    if (e.target.value === "M") {
      $("#id_viscosidad").removeAttr("disabled");
      $("#id_presion_vapor").removeAttr("disabled");
      $("#id_densidad").removeAttr("disabled");
    } else {
      $("#id_viscosidad").attr("disabled", "disabled");
      $("#id_presion_vapor").attr("disabled", "disabled");
      $("#id_densidad").attr("disabled", "disabled");
    }
  });

  $("#cas_compuesto").keyup((e) => {
    let valor = document.getElementById("cas_compuesto").value;
    if (valor.split("").filter((x) => x === "-").length == 2) {
      $.ajax({
        url: "/auxiliares/consultar_cas/",
        data: {
          cas: document.getElementById("cas_compuesto").value,
        },
        success: (res) => {
          if (res.estado === 1 || res.estado === 2) {
            document.getElementById("nombre_compuesto_cas").value = res.nombre;
            if (res.estado === 1)
              document
                .getElementById("guardar-cas")
                .removeAttribute("disabled");
            else {
              document.getElementById("nombre_compuesto_cas").value +=
                " (Ya Registrado)";
              document
                .getElementById("guardar-cas")
                .setAttribute("disabled", true);
            }
          } else {
            document.getElementById("nombre_compuesto_cas").value =
              "NO ENCONTRADO";
            document
              .getElementById("guardar-cas")
              .setAttribute("disabled", true);
          }
        },
        error: (res) => {
          document.getElementById("nombre_compuesto_cas").value = "";
          document.getElementById("guardar-cas").setAttribute("disabled", true);
        },
      });
    } else {
      document.getElementById("guardar-cas").setAttribute("disabled", true);
    }
  });

  $("#guardar-cas").click((e) => {
    e.preventDefault();
    const compuesto_cas = document.getElementById("nombre_compuesto_cas").value;
    if (compuesto_cas !== "" && compuesto_cas.indexOf("*")) {
      $.ajax({
        url: "/auxiliares/registrar_fluido_cas/",
        data: {
          cas: document.getElementById("cas_compuesto").value,
          nombre: compuesto_cas,
        },
        success: (res) => {
          const valor = res.id;
          document.getElementById(
            "id_fluido"
          ).innerHTML += `<option value="${valor}" selected>${compuesto_cas.toUpperCase()}</option>`;
          $('#id_calculo_propiedades').val("M").trigger("change");
          $('#id_temperatura_operacion').change();
          $("#anadir_fluido_no_registradoClose").click();
        },
        error: (res) => {
          alert("No se pudo registrar el fluido en la base de datos.");
        },
      });
    } else alert("Debe de colocarle un nombre válido al compuesto.");
  });

  $("#id_calculo_propiedades").change((e) => {
    if (e.target.value === "M") $("button[type=submit]").removeAttr("disabled");
  });

  $("#nombre_compuesto").keyup((e) => {
    if (e.target.value !== "") {
      document
        .getElementById("guardar-desconocido")
        .removeAttribute("disabled");
    } else
      document
        .getElementById("guardar-desconocido")
        .setAttribute("disabled", true);
  });

  $("#guardar-desconocido").click((e) => {
    e.preventDefault();
    const valor = `${document.getElementById("nombre_compuesto").value}`;
    document.getElementById(
      "id_fluido"
    ).innerHTML += `<option value selected>${document
      .getElementById("nombre_compuesto")
      .value.toUpperCase()}</option>`;

    $("#id_nombre_fluido").val(valor);
    document.getElementById("nombre_compuesto").value = "";
    $("#id_calculo_propiedades").html("<option value='M'>Manual</option>");
    $("#id_calculo_propiedades").change();
    $("#anadir_fluido_no_registradoClose").click();
  });

  $("#id_fluido").change((e) => {
    if (document.getElementById("id_fluido").value !== "") {
      $("#id_nombre_fluido").val("");
      $("#id_calculo_propiedades").html(
        "<option value='A'>Automático</option><option value='M'>Manual</option>"
      );
    } else {
      $("#id_calculo_propiedades").html("<option value='M'>Manual</option>");
      $("#id_viscosidad").removeAttr("disabled");
      $("#id_presion_vapor").removeAttr("disabled");
      $("#id_densidad").removeAttr("disabled");
      $("button[type=submit]").removeAttr("disabled");
      $("#id_nombre_fluido").val(
        e.target.querySelector("option:checked").innerHTML
      );
    }
  });
}

const anadir_listeners_htmx = () => {
  document.body.addEventListener("htmx:beforeRequest", function (evt) {
    const body = document.getElementsByTagName("body")[0];
    body.style.opacity = 0.25;

    if (evt.target.id === "id_complejo") {
      return;
    }

    if (
      document.getElementById("id_calculo_propiedades").value === "M" ||
      document.getElementById("id_temperatura_presion_vapor").value === "" ||
      document.getElementById("id_fluido").value === "" ||
      isNaN(Number(document.getElementById("id_fluido").value)) ||
      document.getElementById("id_temperatura_operacion").value === "" ||
      document.getElementById("id_presion_succion").value === ""
    ) {
      evt.preventDefault();
      if (document.getElementById("id_calculo_propiedades").value === "M") {
        $("#id_viscosidad").removeAttr("disabled");
        $("#id_presion_vapor").removeAttr("disabled");
        $("#id_densidad").removeAttr("disabled");
        $("#aviso").html("");
      }
      body.style.opacity = 1.0;
    } else $("button[type=submit]").attr("disabled", "disabled");
  });

  document.body.addEventListener("htmx:afterRequest", function (evt) {
    if (evt.detail.failed) {
      alert(
        "Ha ocurrido un error al momento de llevar a cabo los cálculos de las propiedades termodinámicas. Verifique que los datos corresponden a la fase líquida del fluido ingresado y no sobrepase la temperatura crítica."
      );
      $("button[type=submit]").attr("disabled", "disabled");
      $("#id_viscosidad").val("");
      $("#id_presion_vapor").val("");
      $("#id_densidad").val("");
      $("#aviso").html("");
      document.body.style.opacity = 1.0;
    } else $("button[type=submit]").removeAttr("disabled");
  });
};

document.body.addEventListener("htmx:afterRequest", function (evt) {
  document.body.style.opacity = 1.0;
});

$("#submit").click((e) => {
  if (!confirm("¿Está seguro que desea realizar esta acción?"))
    e.preventDefault();
    
});

$("form").submit((e) => {
  $("#submit").attr("disabled", "disabled");
});

anadir_listeners_htmx();
anadir_listeners_dropboxes();