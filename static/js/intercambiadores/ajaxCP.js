// Lógica de cuando se registrará un nuevo fluido

function anadir_listeners_registro() {
    $('.no-submit').click((e) => {
        e.preventDefault();
    });
    
    $('#cas_compuesto_tubo').keyup((e) => {
        let valor = document.getElementById('cas_compuesto_tubo').value;
        if(valor.split('').filter(x => x === '-').length == 2){
            $.ajax({
                url: '/intercambiadores/consultar_cas/', data: {
                    'cas': document.getElementById('cas_compuesto_tubo').value
                }, success: (res) => {
                    if(res.estado === 1 || res.estado === 2){
                        document.getElementById('nombre_compuesto_tubo_cas').value = res.nombre;
                        if(res.estado === 1)
                            document.getElementById('guardar_datos_cas_tubo').removeAttribute('disabled');
                        else{
                            document.getElementById('nombre_compuesto_tubo_cas').value += " (Ya Registrado)";
                            document.getElementById('guardar_datos_cas_tubo').setAttribute('disabled', true);
                        }
                    } else{
                        document.getElementById('nombre_compuesto_tubo_cas').value = "NO ENCONTRADO";
                        document.getElementById('guardar_datos_cas_tubo').setAttribute('disabled', true);
                    }
                }, error: (res) => {
                    document.getElementById('nombre_compuesto_tubo_cas').value = '';
                    document.getElementById('guardar_datos_cas_tubo').setAttribute('disabled', true);
                }
            });
        } else{
            document.getElementById('guardar_datos_cas_tubo').setAttribute('disabled', true);
        }
    });
    
    $('#cas_compuesto_carcasa').keyup((e) => {
        let valor = document.getElementById('cas_compuesto_carcasa').value;
        if(valor.split('').filter(x => x === '-').length == 2){
            $.ajax({
                url: '/intercambiadores/consultar_cas/', data: {
                    'cas': document.getElementById('cas_compuesto_carcasa').value
                }, success: (res) => {
                    if(res.estado === 1 || res.estado === 2){
                        document.getElementById('nombre_compuesto_carcasa_cas').value = res.nombre;
                        if(res.estado === 1)
                            document.getElementById('guardar_datos_cas_carcasa').removeAttribute('disabled');
                        else{
                            document.getElementById('nombre_compuesto_carcasa_cas').value += " (Ya Registrado)";
                            document.getElementById('guardar_datos_cas_carcasa').setAttribute('disabled', true);
                        }
                    } else{
                        document.getElementById('nombre_compuesto_carcasa_cas').value = "NO ENCONTRADO";
                        document.getElementById('guardar_datos_cas_carcasa').setAttribute('disabled', true);
                    }
                }, error: (res) => {
                    document.getElementById('nombre_compuesto_carcasa_cas').value = '';
                    document.getElementById('guardar_datos_cas_carcasa').setAttribute('disabled', true);
                }
            });
        } else{
            document.getElementById('guardar_datos_cas_carcasa').setAttribute('disabled', true);
        }
    });
    
    $('#guardar_datos_cas_carcasa').click((e) => {
        if(document.getElementById('nombre_compuesto_carcasa_cas').value !== '' && document.getElementById('nombre_compuesto_carcasa_cas').value.indexOf('*')){
            const valor = `${document.getElementById('nombre_compuesto_carcasa_cas').value}*${document.getElementById('cas_compuesto_carcasa').value}`;
            document.getElementById('fluido_carcasa').innerHTML += `<option value="${valor}" selected>${document.getElementById('nombre_compuesto_carcasa_cas').value.toUpperCase()}</option>`;
            actualizar_tipos('C');

            if($('#temp_out_carcasa').val() !== '' && $('#temp_in_carcasa').val() !== '')
               ajaxCPCarcasa();

            document.getElementById('nombre_compuesto_carcasa_cas').value = '';
            document.getElementById('cas_compuesto_carcasa').value = '';
            
            $('#condiciones_diseno_fluido_carcasaClose').click();
        } else
            alert("Debe de colocarle un nombre válido al compuesto.");
    });
    
    $('#guardar_datos_cas_tubo').click((e) => {
        if(document.getElementById('nombre_compuesto_tubo_cas').value !== '' && document.getElementById('nombre_compuesto_tubo_cas').value.indexOf('*')){
            const valor = `${document.getElementById('nombre_compuesto_tubo_cas').value}*${document.getElementById('cas_compuesto_tubo').value}`;
            document.getElementById('fluido_tubo').innerHTML += `<option value="${valor}" selected>${document.getElementById('nombre_compuesto_tubo_cas').value.toUpperCase()}</option>`;
            actualizar_tipos('T');
            if($('#temp_out_tubo').val() !== '' && $('#temp_in_tubo').val() !== '')
                ajaxCPTubo();

            document.getElementById('nombre_compuesto_tubo_cas').value = '';
            document.getElementById('cas_compuesto_tubo').value = '';
            
            $('#condiciones_diseno_fluido_tuboClose').click();
        } else
            alert("Debe de colocarle un nombre válido al compuesto.");
    });
    
    $('#nombre_compuesto_tubo').keyup((e) => {
        if(e.target.value !== '' && $('#cp_compuesto_tubo').val() !== ''){
            document.getElementById('enviar_compuesto_tubo_ficha').removeAttribute('disabled');
        } else
            document.getElementById('enviar_compuesto_tubo_ficha').setAttribute('disabled', true);               
    });
    
    $('#cp_compuesto_tubo').keyup((e) => {
        if(e.target.value !== '' && $('#nombre_compuesto_tubo').val() !== ''){
            document.getElementById('enviar_compuesto_tubo_ficha').removeAttribute('disabled');
        } else
            document.getElementById('enviar_compuesto_tubo_ficha').setAttribute('disabled', true);            
    });
    
    $('#enviar_compuesto_tubo_ficha').click((e) => {
        const valor = `${document.getElementById('nombre_compuesto_tubo').value}*${document.getElementById('cp_compuesto_tubo').value}`;
        const cambio_fase = $('#cambio_fase_tubo').val();

        document.getElementById('fluido_tubo').innerHTML += `<option value="${valor}" selected>${document.getElementById('nombre_compuesto_tubo').value.toUpperCase()}</option>`;

        if(cambio_fase === 'S'){
            // De acuerdo a lo flujos dados determinar cual se activa y desactiva
            if(Number($('#flujo_liquido_in_tubo').val()) !== 0 && Number($('#flujo_liquido_in_tubo').val()) === Number($('#flujo_liquido_out_tubo').val())){
                $('#cp_liquido_tubo').removeAttr('disabled');
                $('#cp_liquido_tubo').val(document.getElementById('cp_compuesto_tubo').value);
                $('#cp_gas_tubo').attr('disabled', true);
                $('#cp_gas_tubo').val('');             
            }
            else if(Number($('#flujo_vapor_in_tubo').val()) !== 0 && Number($('#flujo_vapor_in_tubo').val()) === Number($('#flujo_vapor_out_tubo').val())){
                $('#cp_gas_tubo').removeAttr('disabled');
                $('#cp_gas_tubo').val(document.getElementById('cp_compuesto_tubo').value);
                $('#cp_liquido_tubo').attr('disabled', true);
                $('#cp_liquido_tubo').val('');            
            }
        }
        else if (cambio_fase !== '-'){
            $('#cp_liquido_tubo').removeAttr('disabled');
            $('#cp_gas_tubo').removeAttr('disabled');
            document.getElementById('cp_liquido_tubo').value = document.getElementById('cp_compuesto_tubo').value;
            document.getElementById('cp_gas_tubo').value = document.getElementById('cp_compuesto_tubo').value;
        }

        $('#nombre_compuesto_tubo').val('');
        $('#cp_compuesto_tubo').val('');

        $('#condiciones_diseno_fluido_tuboClose').click();
        actualizar_tipos('T');
    });
    
    $('#nombre_compuesto_carcasa').keyup((e) => {
        if(e.target.value !== '' && $('#cp_compuesto_carcasa').val() !== ''){
            document.getElementById('enviar_compuesto_carcasa_ficha').removeAttribute('disabled');
        } else
            document.getElementById('enviar_compuesto_carcasa_ficha').setAttribute('disabled', true);               
    });
    
    $('#cp_compuesto_carcasa').keyup((e) => {
        if(e.target.value !== '' && $('#nombre_compuesto_carcasa').val() !== ''){
            document.getElementById('enviar_compuesto_carcasa_ficha').removeAttribute('disabled');
        } else
            document.getElementById('enviar_compuesto_carcasa_ficha').setAttribute('disabled', true);            
    });
    
    $('#enviar_compuesto_carcasa_ficha').click((e) => {
        const valor = `${document.getElementById('nombre_compuesto_carcasa').value}*${document.getElementById('cp_compuesto_carcasa').value}`;
        const cambio_fase = $('#cambio_fase_carcasa').val();
        document.getElementById('fluido_carcasa').innerHTML += `<option value="${valor}" selected>${document.getElementById('nombre_compuesto_carcasa').value.toUpperCase()}</option>`;
        
        if(cambio_fase === 'S'){
            // De acuerdo a lo flujos dados determinar cual se activa y desactiva
            if(Number($('#flujo_liquido_in_carcasa').val()) !== 0 && Number($('#flujo_liquido_in_carcasa').val()) === Number($('#flujo_liquido_out_carcasa').val())){
                $('#cp_liquido_carcasa').removeAttr('disabled');
                $('#cp_liquido_carcasa').val(document.getElementById('cp_compuesto_carcasa').value);
                $('#cp_gas_carcasa').attr('disabled', true);
                $('#cp_gas_carcasa').val('');             
            }
            else if(Number($('#flujo_vapor_in_carcasa').val()) !== 0 && Number($('#flujo_vapor_in_carcasa').val()) === Number($('#flujo_vapor_out_carcasa').val())){
                $('#cp_gas_carcasa').removeAttr('disabled');
                $('#cp_gas_carcasa').val(document.getElementById('cp_compuesto_carcasa').value);
                $('#cp_liquido_carcasa').attr('disabled', true);  
                $('#cp_liquido_carcasa').val('');          
            }
        }
        else if (cambio_fase !== '-'){
            $('#cp_liquido_carcasa').removeAttr('disabled');
            $('#cp_gas_carcasa').removeAttr('disabled');
            document.getElementById('cp_liquido_carcasa').value = document.getElementById('cp_compuesto_carcasa').value;
            document.getElementById('cp_gas_carcasa').value = document.getElementById('cp_compuesto_carcasa').value;
        }

        $('#nombre_compuesto_carcasa').val('')
        $('#cp_compuesto_carcasa').val('')

        $('#condiciones_diseno_fluido_carcasaClose').click();
        actualizar_tipos('C');
    });    
}

// Cálculo de Cp

function ajaxCP(t1,t2,fluido, lado = 'T'){
    if(lado === 'T' && $('#cambio_fase_tubo').val() !== '-' && $('#tipo_cp_tubo').val() === 'A' 
    || lado === 'C' && $('#cambio_fase_carcasa').val() !== '-' && $('#tipo_cp_carcasa').val() === 'A'){
        let cambio_fase = lado === 'C' ? $('#cambio_fase_carcasa').val() : $('#cambio_fase_tubo').val();
        document.body.style.opacity = 0.5;
        $.ajax({
            url: '/intercambiadores/calcular_cp/',
            data: {
                t1,
                t2,
                fluido,
                unidad: $('#unidad_temperaturas').val(),
                unidad_salida: $('#unidad_cp').val(),
                cambio_fase,
                presion: lado === 'C' ? $('#presion_entrada_carcasa').val() : $('#presion_entrada_tubo').val(),
                unidad_presiones: $('#unidad_presiones').val(),
                flujo_vapor_in: lado === 'C' ? $('#flujo_vapor_in_carcasa').val() : $('#flujo_vapor_in_tubo').val(),
                flujo_vapor_out: lado === 'C' ? $('#flujo_vapor_out_carcasa').val() : $('#flujo_vapor_out_tubo').val(),
                flujo_liquido_in: lado === 'C' ? $('#flujo_liquido_in_carcasa').val() : $('#flujo_liquido_in_tubo').val(),
                flujo_liquido_out: lado === 'C' ? $('#flujo_liquido_out_carcasa').val() : $('#flujo_liquido_out_tubo').val()
            },
            success: (res) => {
                document.body.style.opacity = 1.0;
                if(lado === 'T'){
                    if(cambio_fase !== '-' && res.cp !== '' && $('#cambio_fase_carcasa').val() !== '-')
                        $('button[type="submit"]').removeAttr('disabled');

                    if(cambio_fase === 'S')
                        if(Number($('#flujo_vapor_in_tubo').val()) !== 0){
                            $('#cp_gas_tubo').val(res.cp_gas);
                            $('#cp_liquido_tubo').val('');
                        }
                        else{
                            $('#cp_liquido_tubo').val(res.cp_liquido);
                            $('#cp_gas_tubo').val('');
                        }
                    else{                        
                        $('#cp_liquido_tubo').val(res.cp_liquido);
                        $('#cp_gas_tubo').val(res.cp_gas);
                    }
                }
                else{
                    if(cambio_fase !== '-' && res.cp !== '' && $('#cambio_fase_tubo').val() !== '-')
                        $('button[type="submit"]').removeAttr('disabled');

                    if(cambio_fase === 'S')
                        if(Number($('#flujo_vapor_in_carcasa').val()) !== 0){
                            $('#cp_gas_carcasa').val(res.cp_gas);
                            $('#cp_liquido_carcasa').val('');
                        }
                        else{
                            $('#cp_liquido_carcasa').val(res.cp_liquido);
                            $('#cp_gas_carcasa').val('');
                        }
                    else{                        
                        $('#cp_liquido_carcasa').val(res.cp_liquido);
                        $('#cp_gas_carcasa').val(res.cp_gas);
                    }
                }
            }, 
            error: (res) => {
                document.body.style.opacity = 1.0;
                $('button[type="submit"]').attr('disabled', true);
            }
        });
    }
}

function ajaxCPCarcasa(){
    if($('#temp_out_carcasa').val() !== '' && $('#temp_in_carcasa').val() !== '' && $('#fluido_carcasa').val() !== ''){
        ajaxCP($('#temp_in_carcasa').val(), $('#temp_out_carcasa').val(), $('#fluido_carcasa').val(), 'C');
    }
}

function ajaxCPTubo(){
    if($('#temp_out_tubo').val() !== '' && $('#temp_in_tubo').val() !== '' && $('#fluido_tubo').val() !== ''){
        ajaxCP($('#temp_in_tubo').val(), $('#temp_out_tubo').val(), $('#fluido_tubo').val(), 'T');
    }
}

function anadir_listeners_cp() {
    $('#temp_in_carcasa').keyup((e) => {
        ajaxCPCarcasa();
    });
    
    $('#temp_out_carcasa').keyup((e) => {
        ajaxCPCarcasa();
    });
    
    $('#fluido_carcasa').change((e) => {
        if($('#temp_out_carcasa').val() !== '' && $('#temp_in_carcasa').val() !== '' && $('#fluido_carcasa').val() !== ''){
            const val = $('#fluido_carcasa').val();

            if(Number(val))
                ajaxCPCarcasa();
            else{
                const splitted = val.split('*');
                if(Number(splitted[1]))
                   console.log("carcasa");
                else
                    ajaxCP($('#temp_in_carcasa').val(), $('#temp_out_carcasa').val(), val, 'C');
            }
        }

        actualizar_tipos('C');

        if($('#cambio_fase_carcasa').val() === 'T' && $('#tipo_cp_carcasa').val() === 'M'
            && ($('#fluido_carcasa').val() === '' || $('#fluido_carcasa').val().includes('*')&& !$('#fluido_carcasa').val().split('*')[1].includes('-')))
            $('#sat_carcasa').removeAttr('hidden');
        else
            $('#sat_carcasa').attr('hidden', true);
    });
    
    $('#temp_in_tubo').keyup((e) => {
        ajaxCPTubo();
    });
    
    $('#temp_out_tubo').keyup((e) => {
        ajaxCPTubo();
    });
    
    $('#fluido_tubo').change((e) => {
        if($('#temp_out_tubo').val() !== '' && $('#temp_in_tubo').val() !== '' && $('#fluido_tubo').val() !== ''){
            const val = $('#fluido_tubo').val();
            if(Number(val))
                ajaxCPTubo();
            else{
                const splitted = val.split('*');
                if(Number(splitted[1]))
                    console.log("tubo");
                else
                    ajaxCPTubo();
            }
        }

        actualizar_tipos('T');
        if($('#cambio_fase_tubo').val() === 'T' && $('#tipo_cp_tubo').val() === 'M'
            && ($('#fluido_tubo').val() === '' || $('#fluido_tubo').val().includes('*') && $('#fluido_tubo').val().split('*')[1].includes('-'))){
                $('#sat_tubo').removeAttr('hidden');
            }
        else
            $('#sat_tubo').attr('hidden', true);
    });
    
    $('#presion_entrada_carcasa').keyup((e) => {
        ajaxCPCarcasa();
    });
    
    $('#presion_entrada_tubo').keyup((e) => {
        ajaxCPTubo();
    });

    $('#unidad_presiones').change((e) => {
        ajaxCPCarcasa();
        ajaxCPTubo();
    });
}

// Cambio automático de unidades

function anadir_listeners_unidades() {
    $('#unidad_temperaturas').change((e) => {
        if($('#temp_out_carcasa').val() !== '' && $('#temp_in_carcasa').val() !== '' && $('#fluido_carcasa').val() !== ''){
            ajaxCPCarcasa();
        }
    
        if($('#temp_out_tubo').val() !== '' && $('#temp_in_tubo').val() !== '' && $('#fluido_tubo').val() !== ''){
            ajaxCPTubo();
        }
    });
    
    $('#unidad_cp').change((e) => {
        if($('#temp_out_carcasa').val() !== '' && $('#temp_in_carcasa').val() !== '' && $('#fluido_carcasa').val() !== ''){
            ajaxCPCarcasa();
        }
    
        if($('#temp_out_tubo').val() !== '' && $('#temp_in_tubo').val() !== '' && $('#fluido_tubo').val() !== ''){
            ajaxCPTubo();
        }
    });
    
    $('#unidad_temperaturas').change((e) => {
        const array = $('select[name="unidad_temperaturas"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });
    
    $('#unidad_presiones').change((e) => {
        const array = $('select[name="unidad_presiones"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });
    
    $('#unidad_diametros').change((e) => {
        const array = $('select[name="unidad_diametros"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });
    
    $('#unidad_flujos').change((e) => {
        const array = $('select[name="unidad_flujos"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });
    
    $('#unidad_fouling').change((e) => {
        const array = $('select[name="unidad_fouling"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });
    
    $('#unidad_cp').change((e) => {
        const array = $('select[name="unidad_cp"]').toArray().slice(1);
    
        array.map((x) => {
            x.innerHTML = "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });    
}

function anadir_listeners() {
    anadir_listeners_registro();
    anadir_listeners_cp();
    anadir_listeners_unidades();
}

function actualizar_tipos(lado = "T") { // Actualización de Tipos de Cálculo de Cp
    const id = lado === 'T' ? '#tipo_cp_tubo' : '#tipo_cp_carcasa';
    const id_fluido = lado === 'T' ? '#fluido_tubo' : '#fluido_carcasa';
    const id_cdf = lado === 'T' ? '#cambio_fase_tubo' : '#cambio_fase_carcasa';
    const id_tsat_hvap = lado === 'T' ? '#sat_tubo' : '#sat_carcasa';
    $(id).empty();

    if($(id_fluido).val() === '' || $(id_fluido).val().includes("*")){
        $(id).html(`
            <option value="M">Manual</option>
        `);

        if($(id_cdf).val() === 'S'){
            cambiar_accesibilidad_por_fase(lado);
        }
        else{
            const id_cp_liq = lado === 'T' ? '#cp_liquido_tubo' : '#cp_liquido_carcasa';
            const id_cp_gas = lado === 'T' ? '#cp_gas_tubo' : '#cp_gas_carcasa';
            $(id_cp_liq).removeAttr('disabled');  
            $(id_cp_gas).removeAttr('disabled');   
            
            if($(id_cdf).val() === 'T')
                $(id_tsat_hvap).removeAttr('hidden');

        }
        
    } else{
        $(id).html(`
            <option value="A">Automático</option>
            <option value="M">Manual</option>
        `);

        const id_cp_liq = lado === 'T' ? '#cp_liquido_tubo' : '#cp_liquido_carcasa';
        const id_cp_gas = lado === 'T' ? '#cp_gas_tubo' : '#cp_gas_carcasa';
        $(id_tsat_hvap).attr('hidden', true);
        $(id_cp_liq).attr('disabled', true);  
        $(id_cp_gas).attr('disabled', true);  
        if(lado == "C")
            ajaxCPCarcasa();
        else
            ajaxCPTubo          
    }
}

anadir_listeners();

const validarForm = (e) => {
    if($('#presion_entrada_carcasa').val() === 0){
        alert("La presión de entrada de la carcasa no puede ser 0.");
        return false;
    }

    if($('#presion_entrada_tubo').val() === 0){
        alert("La presión de entrada del tubo no puede ser 0.");
        return false;
    }

    if($('#cambio_fase_carcasa').val() == 'T' && $('#tipo_cp_carcasa').val() === 'M'
        && ($('#fluido_carcasa').val() === '' || $('#fluido_carcasa').val().indexOf('*') !== -1 && $('#fluido_carcasa').val().split('*')[1].indexOf('-') === -1)){
        if($('#hvap_carcasa').val() === '' && $('#tsat_carcasa').val() === ''){
            alert("Debe ingresar la temperatura de saturación del fluido de la carcasa y/o el calor latente del mismo.")
            return false;
        }
    }

    if($('#cambio_fase_carcasa').val() == 'P' && Number($('#flujo_vapor_in_carcasa').val()) && Number($('#flujo_vapor_out_carcasa').val())
        && Number($('#flujo_liquido_in_carcasa').val()) && Number($('#flujo_liquido_out_carcasa').val())
        && Number($('#temp_in_carcasa').val()) !== Number($('#temp_out_carcasa').val())
        && !($('#fluido_carcasa').val() === '' || $('#fluido_carcasa').val().indexOf('*') !== -1 && $('#fluido_carcasa').val().split('*')[1].indexOf('-') === -1)){
        if(!confirm("Lado Carcasa:\n Las temperaturas no deberían ser distintas en un cambio de fase parcial dentro del domo. ¿Desea continuar igualmente?"))
            return false;
    }

    if($('#cambio_fase_tubo').val() == 'T' && $('#tipo_cp_tubo').val() === 'M'
        && ($('#fluido_tubo').val() === '' || $('#fluido_tubo').val().indexOf('*') !== -1 && $('#fluido_tubo').val().split('*')[1].indexOf('-') === -1)){
        if($('#hvap_tubo').val() === '' && $('#tsat_tubo').val() === ''){
            alert("Debe ingresar la temperatura de saturación del fluido del tubo y/o el calor latente del mismo.")
            return false;
        }
    }

    if($('#cambio_fase_tubo').val() == 'P' && Number($('#flujo_vapor_in_tubo').val()) && Number($('#flujo_vapor_out_tubo').val())
        && Number($('#flujo_liquido_in_tubo').val()) && Number($('#flujo_liquido_out_tubo').val())
        && Number($('#temp_in_tubo').val()) !== Number($('#temp_out_tubo').val()) 
        && !($('#fluido_tubo').val() === '' || $('#fluido_tubo').val().indexOf('*') !== -1 && $('#fluido_tubo').val().split('*')[1].indexOf('-') === -1)){
        
        if(!confirm("Lado Tubo:\n Las temperaturas no deberían ser distintas en un cambio de fase parcial dentro del domo. ¿Desea continuar igualmente?"))
            return false;
    }

    if(Number($('#flujo_vapor_in_tubo').val()) > Number($('#flujo_vapor_out_tubo').val())
        && Number($('#temp_in_tubo').val()) < Number($('#temp_out_tubo').val())){
        if(!confirm("Lado Tubo:\n Al presentarse una condensación las temperaturas no deberían aumentar. ¿Desea continuar igualmente?"))
            return false;
    }

    if(Number($('#flujo_vapor_in_carcasa').val()) > Number($('#flujo_vapor_out_carcasa').val())
        && Number($('#temp_in_carcasa').val()) < Number($('#temp_out_carcasa').val())){
        if(!confirm("Lado Carcasa:\n Al presentarse una condensación las temperaturas no deberían aumentar. ¿Desea continuar igualmente?"))
            return false;
    }

    if(Number($('#flujo_liquido_in_tubo').val()) > Number($('#flujo_liquido_out_tubo').val())
        && Number($('#temp_in_tubo').val()) > Number($('#temp_out_tubo').val())){
        if(!confirm("Lado Tubo:\n Al presentarse una evaporación las temperaturas no deberían disminuir. ¿Desea continuar igualmente?"))
            return false;
    }

    if(Number($('#flujo_liquido_in_carcasa').val()) > Number($('#flujo_liquido_out_carcasa').val())
        && Number($('#temp_in_carcasa').val()) > Number($('#temp_out_carcasa').val())){
        if(!confirm("Lado Carcasa:\n Al presentarse una evaporación las temperaturas no deberían disminuir. ¿Desea continuar igualmente?"))
            return false;
    }

    let mensaje = "";
    let q = 0;
    let n = 0;

    if(Number($('#fluido_tubo').val()) || $('#fluido_tubo').val().includes('*') && $('#fluido_tubo').val().split('*')[1].includes('-') || $('#cambio_fase_tubo').val() === 'S'){
        const res = ajaxValidacion('T');
        mensaje += res[0];
        q += Number(res[1]);
        n++;
    }

    if(Number($('#fluido_carcasa').val()) || $('#fluido_carcasa').val().includes('*') && $('#fluido_carcasa').val().split('*')[1].includes('-') || $('#cambio_fase_carcasa').val() === 'S'){
        const res = ajaxValidacion('C');
        mensaje += res[0]  + '\n';
        q += Number(res[1]);
        n++;
    }

    if(n > 0)
        q /= n;

    if(n !== 0 && Math.abs(q - Number($('#calor').val()))/Number($('#calor').val()) > 0.05)
        mensaje += `El calor ingresado difiere por más de un 5% del valor calculado.\n`;

    if($('#cambio_fase_carcasa').val() === 'T' && $('#tipo_cp_carcasa').val() === 'M' && $('#tsat_carcasa').val() && Number($('#temp_in_carcasa').val()) === Number($('#temp_out_carcasa').val()))
        mensaje += `\nUsted colocó un cambio de fase total del lado de la carcasa donde las temperaturas son iguales, sin embargo especificó una temperatura de saturación. Se utilizará la temperatura de entrada/salida.\n`;

    if($('#cambio_fase_tubo').val() === 'T' && $('#tipo_cp_tubo').val() === 'M' && $('#tsat_tubo').val() && Number($('#temp_in_tubo').val()) === Number($('#temp_out_tubo').val()))
        mensaje += `\nUsted colocó un cambio de fase total del lado del tubo donde las temperaturas son iguales, sin embargo especificó una temperatura de saturación. Se utilizará la temperatura de entrada/salida.\n`;

    if(mensaje.trim() !== ''){
        mensaje = "ADVERTENCIA\n" + mensaje + "\n¿Desea continuar igualmente?"
        return confirm(mensaje);
    }

    $('button[type="submit"]').attr('disabled','disabled');

    return true;
};

function ajaxValidacion(lado = 'C'){
    let mensaje = "";
    let q = 0;
    document.body.style.opacity = 0.5;
    $.ajax({
        url: '/intercambiadores/validar_cdf_existente/',
        async: false,
        data: {
            flujo_vapor_in: lado === 'T' ? $('#flujo_vapor_in_tubo').val() : $('#flujo_vapor_in_carcasa').val(),
            flujo_vapor_out: lado === 'T' ? $('#flujo_vapor_out_tubo').val() : $('#flujo_vapor_out_carcasa').val(),
            flujo_liquido_in: lado === 'T' ? $('#flujo_liquido_in_tubo').val() : $('#flujo_liquido_in_carcasa').val(),
            flujo_liquido_out: lado === 'T' ? $('#flujo_liquido_out_tubo').val() : $('#flujo_liquido_out_carcasa').val(),
            cambio_fase: lado === 'T' ? $('#cambio_fase_tubo').val() : $('#cambio_fase_carcasa').val(),
            lado: lado,
            unidad_temperaturas: $('#unidad_temperaturas').val(),
            unidad_presiones: $('#unidad_presiones').val(),
            t1: lado === 'T' ? $('#temp_in_tubo').val() : $('#temp_in_carcasa').val(),
            t2: lado === 'T' ? $('#temp_out_tubo').val() : $('#temp_out_carcasa').val(),
            presion: lado === 'T' ? $('#presion_entrada_tubo').val() : $('#presion_entrada_carcasa').val(),
            fluido: lado === 'T' ? $('#fluido_tubo').val() : $('#fluido_carcasa').val(),
            calor: $('#calor').val(),
            unidad_flujos: $('#unidad_flujos').val(),
            unidad_calor: $('#unidad_calor').val() ? $('#unidad_calor').val(): $('#unidad_q').val(),
            unidad_cp: $('#unidad_cp').val(),
            cp_liquido: lado === 'T' ? $('#cp_liquido_tubo').val() : $('#cp_liquido_carcasa').val(),
            cp_gas: lado === 'T' ? $('#cp_gas_tubo').val() : $('#cp_gas_carcasa').val(),
            hvap: lado === 'T' ? $('#hvap_tubo').val() : $('#hvap_carcasa').val()
        },
        success: (res) => {
            document.body.style.opacity = 1;
            q = res.calorcalc;
            if(res.codigo == 400){
                mensaje += res.mensaje;
            }
        },
        error: (res) => {
            document.body.style.opacity = 1;
            funciono = false;
            mensaje += `Ocurrió un error al validar los datos ingresados del lado de${lado === 'T' ? 'l tubo' : ' la carcasa'}.\n`;
        }
    });

    return [mensaje, q];
}