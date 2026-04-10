document.addEventListener('htmx:afterRequest', (evt) => {
    const target = evt.target;
    const number = target.name.replace(/[^0-9]/g, '');
    $(`.form-${number}-unidad`).html(`<option selected>${$(`#id_form-${number}-unidad`).find("option:selected").text()}</option>`);
});

const cambioUnidades = (formPrefix) => {
    $(`#id_${formPrefix}unidad`).change(function(e) {
        $(`.${formPrefix}unidad`).html(`<option selected>${$(this).find("option:selected").text()}</option>`);
    });
    $(`select[name='${formPrefix}unidad']`).change();
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
    let formNum = forms.length - 1;
    let totalForms = document.querySelector(`#id_form-TOTAL_FORMS`);
    totalForms.setAttribute("value", `${formNum}`);
    e.target.parentElement.parentElement.remove();
    reindex();
    cargarEventListeners(false);
    cambioUnidades(`form-${formNum-1}-`);
    document.querySelectorAll(".form").forEach((el, i) => {
        if(i >= formNum - 1) {
            htmx.process(el);
            const tipo_unidad = el.querySelector("select[name$='-unidad']");
            if(tipo_unidad) {
                const event = new Event('change', { bubbles: true });
                tipo_unidad.dispatchEvent(event);
            }
        }
    });    
};
  
const anadir = (e) => {
    let forms = document.querySelectorAll(`.form`);
    let formContainer = document.querySelector(`#id-forms-container`);
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
      .find("button.anadir")
      .removeClass("btn-success")
      .addClass("btn-danger")
      .removeClass("anadir")
      .addClass("eliminar");
    $(newElement).find("button.eliminar").html("-");
  
    reindex(true);
  
    cargarEventListeners(false);
  
    totalForms.setAttribute("value", `${formNum + 1}`);
  
    formPrefix = `form-${formNum}-`;
    $(`#id_${formPrefix}nombre`).val("");
    $(`#id_${formPrefix}tipo_unidad`).val("");
    $(`#id_${formPrefix}carga_25`).val("");
    $(`#id_${formPrefix}carga_50`).val("");
    $(`#id_${formPrefix}carga_75`).val("");
    $(`#id_${formPrefix}carga_100`).val("");
    $(`#id_${formPrefix}unidad`).val("");
    $(`#id_${formPrefix}unidad`).html("<option value=\"\"></option>");
    $(`.${formPrefix}unidad`).html("");

    htmx.process(`#id_form-${formNum}-tipo_unidad`);
    let idField = newElement.querySelector('input[id$="-id"]');
    if (idField) idField.remove();

    cambioUnidades(formPrefix);
};

const cargarEventListeners = (anadirListeners = true) => {
    $(".eliminar").off("click");
    $(".eliminar").click((e) => {
      eliminar(e);
    });

    if (anadirListeners)
      $(".anadir").click((e) => {
        anadir(e);
      });
};

const confirmSubmit = () => {
    return new Promise((resolve, reject) => {
        const confirmSubmitWindow = window.confirm(
            "¿Está seguro que desea agregar estos datos?"
        );

        if (confirmSubmitWindow) {
            resolve();
        } else {
            reject();
        }
    });
};

$("#submit").click(async (e) => {
    const array_nombres = Array.from(document.querySelectorAll(`.nombre-caracteristica`))
    .filter(x => x.value !== '')  
    .map(x => x.value);
    
    if ((new Set(array_nombres)).size !== array_nombres.length){
      e.preventDefault();
      alert("Todas las características adicionales deben tener nombres distintos.");
      return;
    }

    const array_numeros = Array.from(document.querySelectorAll(`.numero`))
    .filter(x => x.value !== '')  
    .map(x => x.value);
    
    if ((new Set(array_numeros)).size !== array_numeros.length){
      e.preventDefault();
      alert("Todas las corrientes deben tener números distintos.");
      return;
    }

    if(!confirm("¿Está seguro que desea realizar esta acción?")) 
        e.preventDefault();
});

cargarEventListeners();
$("#id_form-INITIAL_FORMS").val(0);