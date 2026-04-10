const anadir_listeners_dropboxes = (magnitud, seccion, parte = 'seccion') => {
    const selector =  `select[name='${parte}-${seccion}-${magnitud}_unidad']`;
    $(selector).change((e) => {
        const array = $(selector).toArray().slice(1);
    
        array.map((x) => {
          x.innerHTML =
            "<option>" + $(`#${e.target.id} option:selected`).html() + "</option>";
        });
    });    
}

const anadir_presion_manometrica = (magnitud, seccion, parte = 'seccion') => {
    const selector =  `select[name='${parte}-${seccion}-${magnitud}_unidad']`;
    $(selector).find('option').each((i, e) => {
        e.textContent += 'g';
    });
}

anadir_listeners_dropboxes('entalpia', 'drenaje');
anadir_listeners_dropboxes('entalpia', 'agua');

anadir_listeners_dropboxes('temp', 'drenaje');
anadir_listeners_dropboxes('temp', 'agua');
anadir_listeners_dropboxes('temp', 'vapor');

anadir_listeners_dropboxes('flujo', 'drenaje');

anadir_listeners_dropboxes('presion', 'drenaje');
anadir_listeners_dropboxes('presion', 'agua');
anadir_listeners_dropboxes('presion', 'vapor');

anadir_presion_manometrica('presion', 'drenaje');
anadir_presion_manometrica('presion', 'agua');
anadir_presion_manometrica('presion', 'vapor');


anadir_presion_manometrica('caida_presion', 'drenaje', 'especs');
anadir_presion_manometrica('caida_presion', 'condensado', 'especs');
anadir_presion_manometrica('caida_presion', 'reduccion', 'especs');