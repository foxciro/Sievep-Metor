const cargarEventListeners = (anadirListeners = true) => {
  $(".eliminar").off("click");
  $(".eliminar").click((e) => {
    const formClass = $(e.target).closest("tr").attr("class");
    eliminar(e, formClass);
  });

  if(anadirListeners)
    $(".anadir").click((e) => {
      const formClass = $(e.target).closest("tr").attr("class");
      anadir(e, formClass);
    });
};

const reindex = (anadir = false, formClass="form") => {
  let forms = document.querySelectorAll(`.${formClass}`);
  let formRegex = RegExp(`${formClass}-(\\d)+-`, "g");
  let valores = {};

  for (let i = 0; i < forms.length; i++) {
    let current_prefix = `${formClass}-${i}-`;

    forms[i].querySelectorAll("input,select").forEach((e) => {
      if (!(anadir && i === forms.length - 1 && e.id.indexOf("-id") !== -1))
        valores[e.id.replace(formRegex, current_prefix)] = e.value;
      else valores[e.id.replace(formRegex, current_prefix)] = "";
    });

    if (forms[i].innerHTML.indexOf(current_prefix) === -1) {
      forms[i].innerHTML = forms[i].innerHTML.replace(
        formRegex,
        current_prefix
      );
    }

    forms[i].querySelectorAll("input,select").forEach((e) => {
      e.value = valores[e.id];
    });

    valores = {};
  }
};

const eliminar = (e, formClass) => {  
  let forms = document.querySelectorAll(`.${formClass}`);
  let formNum = forms.length - 1;
  let totalForms = document.querySelector(`#id_${formClass}-TOTAL_FORMS`);
  totalForms.setAttribute("value", `${formNum}`);
  e.target.parentElement.parentElement.remove();
  reindex(false, formClass);
  cargarEventListeners(false);
  
  let lastId = document.querySelector(`#id_${formClass}-${formNum}-id`);
  lastId.remove();
};

const anadir = (e, formClass) => {
  let forms = document.querySelectorAll(`.${formClass}`);
  let formContainer = document.querySelector(`#${formClass}`);
  let totalForms = document.querySelector(`#id_${formClass}-TOTAL_FORMS`);
  let formNum = forms.length - 1;

  let newForm = forms[0].cloneNode(true);
  let formRegex = RegExp(`${formClass}-(\\d)+-`, "g");
  formNum++;
  let formPrefix = `${formClass}-${formNum}-`;

  newForm.innerHTML = newForm.innerHTML.replace(formRegex, formPrefix);

  let newElement;

  newElement = formContainer.insertBefore(
    newForm,
    e.target.parentNode.parentNode.lastSibling
  );

  $(newElement)
    .find("a.anadir")
    .removeClass("btn-success")
    .addClass("btn-danger")
    .removeClass("anadir")
    .addClass("eliminar");
  $(newElement).find("a.eliminar").html("-");

  reindex(true, formClass);

  cargarEventListeners(false);

  totalForms.setAttribute("value", `${formNum + 1}`);

  formPrefix = `${formClass}-${formNum}-`;
  $(`#id_${formPrefix}numero_corriente`).val("");
  $(`#id_${formPrefix}nombre`).val("");
  $(`#id_${formPrefix}entalpia`).val("");
  $(`#id_${formPrefix}flujo`).val("");
  $(`#id_${formPrefix}presion`).val("");
  $(`#id_${formPrefix}temperatura`).val("");
  $(`#id_${formPrefix}fase`).val("");
  $(`#id_${formPrefix}rol`).val("");
  $(`#id_${formPrefix}densidad`).val("");

  if (newElement.querySelector(`#id_${formPrefix}id`)) {
    newElement.querySelector(`#id_${formPrefix}id`).remove();
  }
}

cargarEventListeners();

const validar_flujos = (lado) => {
  let flujo_entrada = 0;
  let flujo_salida = 0;

  const totalFlujos = $(`#id_form-${lado}-TOTAL_FORMS`).val();
  
  for (let index = 0; index < totalFlujos; index++) {
    const flujo = $("#id_form-" + lado + "-" + index + "-flujo").val();
    const rol = $("#id_form-" + lado + "-" + index + "-rol").val();

    console.log(flujo, index);
    

    if(rol == "E")
      flujo_entrada += Number(flujo);
    else
      flujo_salida += Number(flujo);
  }

  console.log(flujo_entrada, flujo_salida);
  

  if(flujo_entrada != flujo_salida) {
    alert(`El flujo de entrada debe ser igual al flujo de salida (${lado.toUpperCase()}).`);
    return false;
  }

  return true;
};

$("button[type=submit]").click((e) => {
  if (!confirm("¿Está seguro que desea realizar esta acción?"))
    e.preventDefault();

  const arrayNumerosCarcasa = $(".numero-corriente-carcasa")
    .toArray()
    .map((x) => x.value);

  let flujos_validos = validar_flujos("carcasa");
  flujos_validos = flujos_validos && validar_flujos("tubos");

  if(!flujos_validos){
    e.preventDefault();
    return;
  }

  const arrayNumerosTubos = $(".numero-corriente-tubos")
    .toArray()
    .map((x) => x.value);
  
  if (new Set(arrayNumerosCarcasa).size !== arrayNumerosCarcasa.length) {
    e.preventDefault();
    alert("Los números de corrientes de la carcasa deben ser TODOS distintos.");
    return;
  }
  if (new Set(arrayNumerosTubos).size !== arrayNumerosTubos.length) {
    e.preventDefault();
    alert("Los números de corrientes de los tubos deben ser TODOS distintos.");
    return;
  }
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

$("#id_flujo_unidad").change((e) => {
  const array = $('select[name="flujo_unidad"]').toArray().slice(1);

  array.map((x) => {
    x.innerHTML =
      "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
  });
});

$("form").submit((e) => {
  $("#submit").attr("disabled", "disabled");
});

$("#id_form-tubos-INITIAL_FORMS").val(0);
$("#id_form-carcasa-INITIAL_FORMS").val(0);