const cambiar_accesibilidad_por_fase = (lado = 'T') => { // Función para colocar la disponibilidad de los Cp de acuerdo al tipo de cambio de fase
    if(lado === 'C'){ // Lado Carcasa
        if(Number($('#flujo_liquido_in_carcasa').val()) !== 0 && Number($('#flujo_liquido_in_carcasa').val()) === Number($('#flujo_liquido_out_carcasa').val())){
            $('#cp_liquido_carcasa').removeAttr('disabled');
            $('#cp_gas_carcasa').val('');
            $('#cp_gas_carcasa').attr('disabled', true);
        }
        else if(Number($('#flujo_vapor_in_carcasa').val()) !== 0 && Number($('#flujo_vapor_in_carcasa').val()) === Number($('#flujo_vapor_out_carcasa').val())){
            $('#cp_gas_carcasa').removeAttr('disabled');
            $('#cp_liquido_carcasa').val('');
            $('#cp_liquido_carcasa').attr('disabled', true);             
        }
    }
    else{ // Lado Tubo
        if(Number($('#flujo_liquido_in_tubo').val()) !== 0 && Number($('#flujo_liquido_in_tubo').val()) === Number($('#flujo_liquido_out_tubo').val())){
            $('#cp_liquido_tubo').removeAttr('disabled');
            $('#cp_gas_tubo').attr('disabled', true);  
            $('#cp_gas_tubo').val('');             
        }
        else if(Number($('#flujo_vapor_in_tubo').val()) !== 0 && Number($('#flujo_vapor_in_tubo').val()) === Number($('#flujo_vapor_out_tubo').val())){
            $('#cp_gas_tubo').removeAttr('disabled');
            $('#cp_liquido_tubo').attr('disabled', true);
            $('#cp_liquido_tubo').val('');             
        }
    }
}

$('#tipo_cp_carcasa').change(() => {
    cambiar_segun_tipo_y_cambio();
});

$('#tipo_cp_tubo').change(() => {
    cambiar_segun_tipo_y_cambio("T");
});

function cambiar_segun_tipo_y_cambio(lado = 'C') { // Cambiar tipos de Cp de acuerdo al tipo de cambio de fase y calculo de cp
    if(lado === 'C'){
        const cambio_fase = $('#cambio_fase_carcasa').val();
        if(cambio_fase !== '-'){ // Verificación de si hay un tipo de cambio de fase puesto
            if($('#tipo_cp_carcasa').val() === 'A'){
                ajaxCPCarcasa();
                $('#cp_liquido_carcasa').attr('disabled',true);
                $('#cp_gas_carcasa').attr('disabled',true);
                $('#sat_carcasa').attr("hidden", true);
                $('#sat_carcasa').val("");
            }
            else{
                if(cambio_fase === 'S')
                    cambiar_accesibilidad_por_fase('C');
                else{ 
                    $('#cp_liquido_carcasa').removeAttr('disabled');
                    $('#cp_gas_carcasa').removeAttr('disabled'); 
                }

                if(cambio_fase === 'T' && ($('#fluido_carcasa').val() === '' || $('#fluido_carcasa').val().includes('*')&& !$('#fluido_carcasa').val().split('*')[1].includes('-')))                
                    $('#sat_carcasa').removeAttr("hidden");
            }
        }
        else{
            $('#cp_liquido_carcasa').attr('disabled',true);
            $('#cp_gas_carcasa').attr('disabled',true);            
        }
    } else if(lado === 'T'){
        const cambio_fase = $('#cambio_fase_tubo').val();
        if(cambio_fase !== '-'){ // Verificación de si hay un tipo de cambio de fase puesto
            if($('#tipo_cp_tubo').val() === 'A'){
                ajaxCPTubo();
                $('#cp_liquido_tubo').attr('disabled',true);
                $('#cp_gas_tubo').attr('disabled',true);
                $('#sat_tubo').attr("hidden", true);
                $('#sat_tubo').val("");
            }
            else{
                if(cambio_fase === 'S')
                    cambiar_accesibilidad_por_fase('T');
                else{
                    $('#cp_liquido_tubo').removeAttr('disabled');
                    $('#cp_gas_tubo').removeAttr('disabled');  
                }
                
                if(cambio_fase === 'T' && ($('#fluido_tubo').val() === '' || $('#fluido_tubo').val().includes('*')&& !$('#fluido_tubo').val().split('*')[1].includes('-')))                
                    $('#sat_tubo').removeAttr("hidden");
            }
        }
        else{
            $('#cp_liquido_tubo').attr('disabled',true);
            $('#cp_gas_tubo').attr('disabled',true);            
        }
    }
}