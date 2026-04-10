document.addEventListener('htmx:beforeRequest', (evt) => {
    document.body.style.opacity = 0.8;

    if (evt.target.name === 'form') {
        const totales = document.querySelectorAll('input.totals');
        const pasa = Array.from(totales).every((input) => input.value == 100);
        console.log(pasa);
        
        if (pasa) {
            if(document.getElementById('submit').value === 'almacenar')
                if (!confirm('¿Está seguro que desea almacenar esta evaluación?')) {
                    evt.preventDefault();
                    document.body.style.opacity = 1.0;
                }
            
            if(document.getElementById('submit').value === 'calcular')
                if (!confirm('¿Está seguro que calcular los resultados?')) {
                    evt.preventDefault();
                    document.body.style.opacity = 1.0;
                }
        } else{
            
            if (!confirm('Los totales de las composiciones no son 100% en todas las etapas. ¿Desea continuar de todos modos?')) {
                evt.preventDefault();
                document.body.style.opacity = 1.0;
                return;
            }
        }
    }
});

document.addEventListener('htmx:afterRequest', (evt) => {
    document.body.style.opacity = 1.0;

    if(evt.detail.failed)
        alert("Ha ocurrido un error al momento de realizar los cálculos. Por favor revise e intente de nuevo.");
});

function actualizarUnidades() {
    document.addEventListener('input', (e)=>{
        if(e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT'){
            document.getElementById('submit').outerHTML = ' <button type="submit" id="submit" name="submit" value="calcular" class="btn btn-danger">Calcular Resultados</button>';
            document.getElementById('resultados').innerHTML = '';
        }
    });

    const selects_flujo_volumetrico_unidad = document.querySelectorAll('select[name*="-flujo_volumetrico_unidad"]');
    selects_flujo_volumetrico_unidad.forEach((select1)=>{
        selects_flujo_volumetrico_unidad.forEach((select2)=>{
            if(select1.name === select2.name && select1 !== select2){
                select1.addEventListener('change', (e)=>{
                    select2.value = e.target.value;
                });
            }
        });
    });

    const selects_temperatura_unidad = document.querySelectorAll('select[name*="-temperatura_unidad"]');
    selects_temperatura_unidad.forEach((select1)=>{
        selects_temperatura_unidad.forEach((select2)=>{
            if(select1.name === select2.name && select1 !== select2){
                select1.addEventListener('change', (e)=>{
                    select2.value = e.target.value;
                });
            }
        });
    });

    const selects_presion_unidad = document.querySelectorAll('select[name*="presion_unidad"]');
    selects_presion_unidad.forEach((select1)=>{
        selects_presion_unidad.forEach((select2)=>{
            if(select1.name === select2.name && select1 !== select2){
                select1.addEventListener('change', (e)=>{
                    select2.value = e.target.value;
                });
            }
        });
    });
}

function sumColumn(index) {
    const table = document.querySelector('#tabla_composiciones');
    const rows = [...table.rows];
    const columns = rows[0].cells.length;
    const totals = Array(columns).fill(0);

    for (let rowIndex = 0; rowIndex < rows.length - 1; rowIndex++) {
        const row = rows[rowIndex];
        const value = parseFloat(row.cells[index].querySelector('input').value) || 0;
        totals[index] += value;
    }    

    const lastRow = rows[rows.length - 1];
    lastRow.cells[index].querySelector('input').value = (Math.round(totals[index] * 100) / 100).toFixed(2);
}

document.addEventListener("DOMContentLoaded", () => {
    for (let columnIndex = 1; columnIndex < [...document.querySelector('#tabla_composiciones').rows[0].cells].length; columnIndex++) {
        sumColumn(columnIndex);
    }
});

document.addEventListener('htmx:afterSwap', (evt) => {
    if (evt.detail.requestConfig.elt.name === 'evaluacion-caso') {
        for (let columnIndex = 1; columnIndex < [...document.querySelector('#tabla_composiciones').rows[0].cells].length; columnIndex++) {
            sumColumn(columnIndex);
        }
    }
    actualizarUnidades();
    addEventListeners();
});

function addEventListeners() {
    for (let columnIndex = 1; columnIndex < [...document.querySelector('#tabla_composiciones').rows[0].cells].length; columnIndex++) {
        const inputs = [];
        for (let rowIndex = 0; rowIndex < [...document.querySelector('#tabla_composiciones').rows].length - 1; rowIndex++) {
            const row = [...document.querySelector('#tabla_composiciones').rows][rowIndex];
            const input = row.cells[columnIndex].querySelector('input');
            input.addEventListener('change', () => sumColumn(columnIndex));
            input.addEventListener('keyup', () => sumColumn(columnIndex));
            inputs.push(input);
        }
    }
        
}

addEventListeners();
actualizarUnidades();