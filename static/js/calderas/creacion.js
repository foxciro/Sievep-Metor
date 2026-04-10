$("#id_especificaciones-caldera-temperatura_unidad").change(() => {
    $("select[name='especificaciones-caldera-temperatura_unidad']").val($("#id_especificaciones-caldera-temperatura_unidad").val())
});

$("#id_especificaciones-caldera-presion_unidad").change(() => {
    $("select[name='especificaciones-caldera-presion_unidad']").val($("#id_especificaciones-caldera-presion_unidad").val())
});

$("#id_tambor-temperatura_unidad").change(() => {
    $("select[name='tambor-temperatura_unidad']").val($("#id_tambor-temperatura_unidad").val())
});

$("#id_sobrecalentador-presion_unidad").change(() => {
    $("select[name='sobrecalentador-presion_unidad']").val($("#id_sobrecalentador-presion_unidad").val())
});

$("#id_sobrecalentador-presion_unidad").change(() => {
    $("select[name='sobrecalentador-presion_unidad']").val($("#id_sobrecalentador-presion_unidad").val())
});

$("#id_dimensiones-caldera-dimensiones_unidad").change(() => {
    $("select[name='dimensiones-caldera-dimensiones_unidad']").val($("#id_dimensiones-caldera-dimensiones_unidad").val())
});

$("#id_tambor-presion_unidad").change(() => {
    $("select[name='tambor-presion_unidad']").val($("#id_tambor-presion_unidad").val())
});

$("#id_chimenea-dimensiones_unidad").change(() => {
    $("select[name='chimenea-dimensiones_unidad']").val($("#id_chimenea-dimensiones_unidad").val())
});

$("#id_tambor-superior-dimensiones_unidad").change(() => {
    $("select[name='tambor-superior-dimensiones_unidad']").val($("#id_tambor-superior-dimensiones_unidad").val())
});

$("#id_tambor-inferior-dimensiones_unidad").change(() => {
    $("select[name='tambor-inferior-dimensiones_unidad']").val($("#id_tambor-inferior-dimensiones_unidad").val())
});

$("#id_combustible-liquido").change(e => {
    if($(e.target).is(':checked'))
        $("#id_combustible-nombre_liquido").removeAttr("disabled");
    else{
        $("#id_combustible-nombre_liquido").val("");
        $("#id_combustible-nombre_liquido").attr("disabled","");
    }
});

$('#submit').click(e => {  
    // Verificar que la suma de ambos porcentajes correspondan al 100%
    const suma_volumen = $('.porc-vol').toArray().reduce((acc, el) => {
        return acc + Number(el.value);
    }, 0).toFixed(2);

    const suma_aire = $('.porc-aire').toArray().reduce((acc, el) => { 
        return acc + Number(el.value);
    }, 0).toFixed(2);

    if(suma_volumen != 100.00){
        e.preventDefault();
        alert("La suma de los porcentajes de volumen en la composición del combustible debe ser igual a 100.");
        return;
    }

    if(suma_aire != 100.00){
        e.preventDefault();
        alert("La suma de los porcentajes de aire en la composición del combustible debe ser igual a 100.");
        return;
    }

    if(!confirm("¿Está seguro que desea realizar esta acción?"))
        e.preventDefault();
});

$('.porc-vol').keyup(e => {
    const suma_volumen = $('.porc-vol').toArray().reduce((acc, el) => {
        return acc + Number(el.value);
    }, 0).toFixed(2);

    $('#total-volumen').val(suma_volumen);

    if(suma_volumen < 100 || suma_volumen > 100)
        $('#submit').attr("disabled","");
    else
        $('#submit').removeAttr("disabled");
});

$('.porc-aire').keyup(e => {
    const suma_aire = $('.porc-aire').toArray().reduce((acc, el) => {
        return acc + Number(el.value);
    }, 0).toFixed(2);

    $('#total-aire').val(suma_aire);

    if(suma_aire < 100 || suma_aire > 100)
        $('#submit').attr("disabled","");
    else
        $('#submit').removeAttr("disabled");
});

$('form').submit(e => {
    $('#submit').attr('disabled','disabled');
});

$('.porc-vol').keyup();
$('.porc-aire').keyup();
$('#id_complejo').change();