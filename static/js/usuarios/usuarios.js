document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('table tbody tr');
    rows.forEach(row => {
        const lecturaCheckbox = row.querySelector('input[name^="planta-"]');
        const lecturaEvaluacionCheckbox = row.querySelector('input[name^="evaluaciones-"]');
        const otherCheckboxes = row.querySelectorAll('input[type="checkbox"]:not([name^="planta-"]):not(input[type="checkbox"][name^="crearevals-"]):not(input[type="checkbox"][name^="delevals-"])');
        const evaluacionCheckboxes = row.querySelectorAll('input[type="checkbox"][name^="crearevals-"], input[type="checkbox"][name^="delevals-"]');

        lecturaCheckbox.addEventListener('change', function() {
            otherCheckboxes.forEach(checkbox => {
                checkbox.disabled = !lecturaCheckbox.checked;
                if (!lecturaCheckbox.checked) {
                    checkbox.checked = false;
                    evaluacionCheckboxes.forEach(checkbox => {
                        checkbox.disabled = true;
                        checkbox.checked = false;
                    })
                }
            });
        });

        lecturaEvaluacionCheckbox.addEventListener('change', function() {
            evaluacionCheckboxes.forEach(checkbox => {
                checkbox.disabled = !lecturaEvaluacionCheckbox.checked;
                if (!lecturaEvaluacionCheckbox.checked) {
                    checkbox.checked = false;
                }
            });
        });

        otherCheckboxes.forEach(checkbox => {
            checkbox.disabled = !lecturaCheckbox.checked || lecturaCheckbox.disabled;
        });

        evaluacionCheckboxes.forEach(checkbox => {
            checkbox.disabled = !lecturaEvaluacionCheckbox.checked || lecturaEvaluacionCheckbox.disabled;
        });
    });

    document.querySelector('input[name="superusuario"]').addEventListener('change', function() {
        const allCheckboxes = document.querySelectorAll('input[type="checkbox"]:not([name="activo"]):not([name="superusuario"])');
        const lecturaCheckboxes = document.querySelectorAll('input[name^="planta-"]');
        if (this.checked) {
            allCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
                checkbox.disabled = false;
            });
        } else {
            allCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.disabled = true;
            });
            lecturaCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
                checkbox.disabled = false;
            });
        }
    });
});

document.querySelector('input[name="superusuario"]').addEventListener('change', function() {
    const superusuarioDeDiv = document.getElementById('superusuario_de');
    if (this.checked) {
        superusuarioDeDiv.classList.remove('d-none');
    } else {
        superusuarioDeDiv.classList.add('d-none');
    }
});

document.querySelector('select[name="superusuario_de"]').addEventListener('change', function() {
    const complejoId = this.value;

    if (complejoId === "todos") {
        const allOtherCheckboxes = document.querySelectorAll(`input[type="checkbox"]:not(input[name="superusuario"]):not(input[name="activo"])`);
        allOtherCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
            checkbox.disabled = true;
            checkbox.dispatchEvent(new Event('change'));
        });
    } else {
        const allOtherCheckboxes = document.querySelectorAll(`input[type="checkbox"]:not(.complejo-${complejoId}):not(input[name="superusuario"]):not(input[name="activo"])`);
        allOtherCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.dispatchEvent(new Event('change'));

            if (checkbox.name.startsWith('planta-')) {
                checkbox.disabled = false;
            }
        });
        
        const checkboxes = document.querySelectorAll(`.complejo-${complejoId}`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            checkbox.disabled = true;
        });  
    } 
});

document.querySelector('form').addEventListener('submit', function(e) {
const activoCheckbox = document.querySelector('input[name="activo"]');
const lecturaCheckboxes = document.querySelectorAll('input[name^="planta-"]');
const isChecked = Array.from(lecturaCheckboxes).some(checkbox => checkbox.checked);

if ((!activoCheckbox || activoCheckbox.checked) && !isChecked) {
    e.preventDefault();
    alert('Debe seleccionar al menos un checkbox en los permisos si el usuario está activo.');
}
});
