$('select[name="volumen_unidad"]').change(function(){
    $('select[name="volumen_unidad"]').val($(this).val());
});

$('select[name="potencia_unidad"]').change(function(){
    $('select[name="potencia_unidad"]').val($(this).val());
});   
$('select[name$="-presion_unidad"]').change(function(){
    $('select[name$="-presion_unidad"]').val($(this).val());
});
$('select[name$="-temp_unidad"]').change(function(){
    $('select[name$="-temp_unidad"]').val($(this).val());
});    