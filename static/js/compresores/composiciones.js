document.addEventListener('DOMContentLoaded', function() {
    const table = document.querySelector('table');
    const rows = [...table.rows];
    const columns = rows[0].cells.length;
    const totals = Array(columns).fill(0);    

    const calculateTotals = () => {
        for (let columnIndex = 1; columnIndex < columns; columnIndex++) {
            totals[columnIndex] = 0;
            for (let rowIndex = 1; rowIndex < rows.length - 2; rowIndex++) {
                const row = rows[rowIndex];
                const input = row.cells[columnIndex].querySelector('.porc-mol');
                const value = parseFloat(input.value) || 0;
                totals[columnIndex] += value;
            }
        }

        const lastRow = rows[rows.length - 1];
        for (let columnIndex = 1; columnIndex < columns; columnIndex++) {
            lastRow.cells[columnIndex].querySelector('input').value = (Math.round(totals[columnIndex] * 100) / 100).toFixed(2);
        }
    }

    for (let columnIndex = 1; columnIndex < columns; columnIndex++) {
        const inputs = [];
        for (let rowIndex = 1; rowIndex < rows.length - 2; rowIndex++) {
            const row = rows[rowIndex];
            const input = row.cells[columnIndex].querySelector('.porc-mol');
            input.addEventListener('change', calculateTotals);
            input.addEventListener('keyup', calculateTotals);
            inputs.push(input);
        }
    }

    calculateTotals();
});

document.body.addEventListener('submit', function(event) {
    const table = document.querySelector('table');
    const rows = [...table.rows];
    const columns = rows[0].cells.length;   

    for (let columnIndex = 1; columnIndex < columns; columnIndex++) {
        const input = rows[rows.length - 1].cells[columnIndex].querySelector('input');
        const value = parseFloat(input.value) || 0;

        console.log(value);
        

        if (value !== 100) {
            event.preventDefault();
            alert("La suma de las cantidades molares de cada etapa debe ser 100%.");
            break;
        }
    }
});
