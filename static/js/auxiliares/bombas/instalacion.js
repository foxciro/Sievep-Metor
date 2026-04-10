const cargarEventListeners = (anadirListeners = true) => {
  $(".eliminar").off("click").click((e) => {
    eliminar(e);
  });


  if (anadirListeners)
    $(".anadir").click((e) => {
      anadir(e);
    });
};

const reindex = (lado, anadir = false) => {
  let forms = document.querySelectorAll(`.${lado}-form`);
  let formRegex = RegExp(`formset-${lado}-(\\d)+-`, "g");
  let valores = {};

  for (let i = 0; i < forms.length; i++) {
    let current_prefix = `formset-${lado}-${i}-`;

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
  const lado =
    e.target.parentElement.parentElement.classList[1] === "succion-form"
      ? "succion"
      : "descarga";
  let forms = document.querySelectorAll(`.${lado}-form`);
  let totalForms = document.querySelector(`#id_formset-${lado}-TOTAL_FORMS`);
  e.target.parentElement.parentElement.remove();
  
  totalForms.setAttribute("value", totalForms.value - 1);
  reindex(lado);
  cargarEventListeners(false);

  let idField = e.target.parentElement.parentElement.querySelector('input[id$="-id"]');
  if(idField) idField.remove();
};

const anadir = (e) => {
  const lado =
    e.target.parentElement.parentElement.parentElement.id === "forms-succion"
      ? "succion"
      : "descarga";
  let forms = document.querySelectorAll(`.${lado}-form`);
  let formContainer = document.querySelector(`#forms-${lado}`);
  let totalForms = document.querySelector(`#id_formset-${lado}-TOTAL_FORMS`);
  let formNum = forms.length - 1;

  let newForm = forms[0].cloneNode(true);
  let formRegex = RegExp(`formset-${lado}-(\\d)+-`, "g");
  let formPrefix = `formset-${lado}-${formNum}-`;

  formNum++;
  newForm.innerHTML = newForm.innerHTML.replace(formRegex, formPrefix);

  let newElement;

  newElement = formContainer.insertBefore(
    newForm,
    e.target.parentNode.parentNode.lastChild.nextSibling
  );

  $(newElement)
    .find("a.anadir")
    .removeClass("btn-success")
    .addClass("btn-danger")
    .removeClass("anadir")
    .addClass("eliminar");
  $(newElement).find("a.eliminar").html("-");

  reindex(lado, true);

  cargarEventListeners(false);

  totalForms.setAttribute("value", `${formNum + 1}`);

  formPrefix = `formset-${lado}-${formNum}-`;
  newElement
    .querySelectorAll("input,select")
    .forEach((e) =>
      e.name.indexOf("unidad") === -1 ? (e.value = "") : e
    );

  if (newElement.querySelector(`#id_${formPrefix}id`)) {
    newElement.querySelector(`#id_${formPrefix}id`).remove();
  }
};

$("button[type=submit]").click((e) => {
  if (!confirm("¿Está seguro que desea realizar esta acción?"))
    e.preventDefault();
});

$(".guardar-accesorios").click((e) => {
  let verificarNegativo = $(".verificar-negativo");
  verificarNegativo.each(function() {
    let valor = Number($(this).val());
    if (isNaN(valor) || valor < 0) {
      alert("No se permiten valores negativos en los campos.");
      e.preventDefault();
    }
  });
});

$(".verificar-negativo").on("change keyup", function(e) {
  let valor = $(this).val();
  if (valor.indexOf("-") !== -1) {
    valor = Math.abs(Number(valor));
    $(this).val(valor);
  }
});

cargarEventListeners();
$("#id_formset-succion-INITIAL_FORMS").val("0");
$("#id_formset-descarga-INITIAL_FORMS").val("0");