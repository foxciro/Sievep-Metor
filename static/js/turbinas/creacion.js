const cargarEventListeners = (anadirListeners = true) => {
  $(".eliminar").off("click");
  $(".eliminar").click((e) => {
    eliminar(e);
  });

  $(".entrada").change((e) => {
    $(".entrada")
      .toArray()
      .filter((el) => !$(el).is(":checked"))
      .map((el) => {
        $(el).attr("disabled", "disabled");
      });
    $(".entrada")
      .toArray()
      .filter((el) => $(el).is(":checked"))
      .map((el) => {
        $(el).removeAttr("disabled");
      });

    if (
      $(".entrada")
        .toArray()
        .filter((el) => !$(el).is(":checked")).length ==
      $(".entrada").toArray().length
    )
      $(".entrada").removeAttr("disabled");
  });

  if (anadirListeners)
    $(".anadir").click((e) => {
      anadir(e);
    });

    $(".fase").change((e) => {
      const number = e.target.name
        .replaceAll("form", "")
        .replaceAll("-", "")
        .replaceAll(/[a-zA-Z]+/g, "");

      const presionInput = $(`input[name='form-${number}-presion']`);
      const temperaturaInput = $(`input[name='form-${number}-temperatura']`);
       
      if ($(e.target).val() === "S") {    
        if (presionInput.val() !== "" && temperaturaInput.val() !== "") {
          presionInput.val("").removeAttr("disabled");
          temperaturaInput.val("").removeAttr("disabled");
        }
    
        presionInput.on('change keyup', function() {
          if ($(this).val() !== "") {
            temperaturaInput.attr("disabled", "disabled");
          } else {
            temperaturaInput.removeAttr("disabled");
          }
        });

        temperaturaInput.on('change keyup', function() {
          if ($(this).val() !== "") {
            presionInput.attr("disabled", "disabled");
          } else {
            presionInput.removeAttr("disabled");
          }
        });
      } else {
        presionInput.removeAttr("disabled").off("change keyup");
        temperaturaInput.removeAttr("disabled").off("change keyup");
      }
    
      $(`input[name='form-${number}-presion'], input[name='form-${number}-temperatura']`).change();
    });
};

const reindex = (anadir = false) => {
  let forms = document.querySelectorAll(`.form`);
  let formRegex = RegExp(`form-(\\d)+-`, "g");
  let valores = {};

  for (let i = 0; i < forms.length; i++) {
    let current_prefix = `form-${i}-`;

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

const eliminar = (e) => {
  let forms = document.querySelectorAll(`.form`);
  let formNum = forms.length;
  let totalForms = document.querySelector(`#id_form-TOTAL_FORMS`);
  totalForms.setAttribute("value", `${formNum - 1}`);
  e.target.parentElement.parentElement.remove();
  reindex();
  cargarEventListeners(false);
  $(".entrada").change();
};

const anadir = (e) => {
  let forms = document.querySelectorAll(`.form`);
  let formContainer = document.querySelector(`#forms-corrientes`);
  let totalForms = document.querySelector(`#id_form-TOTAL_FORMS`);
  let formNum = forms.length - 1;

  let newForm = forms[0].cloneNode(true);
  let formRegex = RegExp(`form-(\\d)+-`, "g");
  formNum++;
  let formPrefix = `form-${formNum}-`;

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

  reindex(true);

  cargarEventListeners(false);

  totalForms.setAttribute("value", `${formNum + 1}`);

  formPrefix = `form-${formNum}-`;
  $(`#id_${formPrefix}numero_corriente`).val("");
  $(`#id_${formPrefix}descripcion_corriente`).val("");
  $(`#id_${formPrefix}entalpia`).val("");
  $(`#id_${formPrefix}flujo`).val("");
  $(`#id_${formPrefix}presion`).val("");
  $(`#id_${formPrefix}temperatura`).val("");
  $(`#id_${formPrefix}fase`).val("");
  $(`#id_${formPrefix}entrada`).removeAttr("checked");

  $(".entrada").change();
};

cargarEventListeners();

$("button[type=submit]").click((e) => {
  let vaporSaturado = 0;
  $(".fase").each(function(){
    if($(this).val() === "S"){
      vaporSaturado++;
    }
  });

  if(vaporSaturado === 0){
    e.preventDefault();
    alert("Debe haber al menos una corriente en vapor saturado.");
    return;
  } 

  let entradas = 0;
  $(".entrada").each(function(){
    if($(this).is(":checked")){
      entradas++;
    }
  });

  if (entradas > 1) {
    e.preventDefault();
    alert("Solo puede haber una corriente de entrada.");
    return;
  } else if (entradas === 0) {
    e.preventDefault();
    alert("Debe haber una corriente de entrada.");
    return;
  }

  const arrayNumeros = $(".numero-corriente")
    .toArray()
    .map((x) => x.value);
  if (new Set(arrayNumeros).size !== arrayNumeros.length) {
    e.preventDefault();
    alert("Los números de corrientes deben ser TODOS distintos.");
    return;
  }

  if (entradas === 1) {
    const entrada = $(".entrada")
      .toArray()
      .filter((x) => $(`#${x.id}`).is(":checked"))[0];
    const number = entrada.name
      .replaceAll("form", "")
      .replaceAll("-", "")
      .replaceAll(/[a-zA-Z]+/g, "");

    if ($(`select[name="form-${number}-fase"]`).val() != "V") {
      e.preventDefault();
      alert("La turbina solo puede tener vapor en la corriente de entrada.");
      return;
    }

    const flujos = $(".flujo").toArray();
    let flujo_sumas = 0;
    let flujo_entrada = 0;

    flujos.forEach((x) => {
      const number_form = x.name
        .replaceAll("form", "")
        .replaceAll("-", "")
        .replaceAll(/[a-zA-Z]+/g, "");
      if (number_form === number) flujo_entrada = Number(x.value);
      else flujo_sumas += Number(x.value);
    });

    flujo_entrada = Number(flujo_entrada.toFixed(5));
    flujo_sumas = Number(flujo_sumas.toFixed(5));

    if (flujo_entrada !== flujo_sumas) {
      e.preventDefault();
      alert(
        `El flujo de entrada debe ser igual a las sumas de los demás flujos: ${flujo_entrada} es distinto de ${flujo_sumas}.`
      );
    }
  }
});

$("#id_potencia_unidad").change((e) => {
  const array = $('select[name="potencia_unidad"]').toArray().slice(1);

  array.map((x) => {
    x.innerHTML =
      "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
  });
});

$("form").submit((e) => {
  $("#submit").attr("disabled", "disabled");
});

const anadir_presion_manometrica = () => {
  const selector =  `select[name='presion_entrada_unidad']`;
  $(selector).find('option').each((i, e) => {
      e.textContent += 'g';
  });
}

anadir_presion_manometrica();
$('.fase').change();