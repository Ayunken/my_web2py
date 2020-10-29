jQuery(document).ready(function(){
$( "#mod_cmp_cmp").keyup(function( event ) {
 $('#_autocomplete_DESCRI_auto').val('');
 var e=event.which?event.which:event.keyCode;
 function F_autocomplete_DESCRI(){
	if ($('#_autocomplete_DESCRI').val()!='-1') 
		{$('#mod_cmp_cmp').val($('#_autocomplete_DESCRI :selected').text());$('#_autocomplete_DESCRI_auto').val($('#_autocomplete_DESCRI').val())} 
	else {$('#mod_cmp_cmp_dialog-form').dialog('open');
		  web2py_component('/Modulero/default/referenced_data.load/mod_cmp_cmp/new/PRODUCTOS?_signature=ead9e2d2fc0acf70fa0be391754d5687955db4e5&field=DESCRI&name='+escape($('#mod_cmp_cmp').val()),'mod_cmp_cmp_dialog-form');
		}
 };

 if (e==13){
	F_autocomplete_DESCRI();
    event.preventDefault();}
	else if (e==40) {if($('#_autocomplete_DESCRI option:selected').next('option').length>0) 
			$('#_autocomplete_DESCRI option:selected').removeAttr('selected').next().attr('selected','selected'); 
          else {$('#_autocomplete_DESCRI option:first').attr('selected','selected')}}
	else if (e==38) {
		if($('#_autocomplete_DESCRI option:selected').prev('option').length>0) {
				$('#_autocomplete_DESCRI option:selected').removeAttr('selected').prev().attr('selected','selected')};  }
	else if ($('#mod_cmp_cmp').val().length>=2) 
			$.get('/Modulero/default/grid_mod_cmp.load/edit/mod_cmp/3?_autocomplete_DESCRI='+escape($('#mod_cmp_cmp').val()),function(data){
					if(data=='') $('#_autocomplete_DESCRI_auto').val('');else{$('#mod_cmp_cmp').next('.error').hide(); $('#_autocomplete_DESCRI_div').html(data).show().focus();$('#_autocomplete_DESCRI_div select').css('width',$('#mod_cmp_cmp').css('width'));$('#_autocomplete_DESCRI_auto').val($('#_autocomplete_DESCRI').val());$('#_autocomplete_DESCRI').change(F_autocomplete_DESCRI);$('#_autocomplete_DESCRI').click(F_autocomplete_DESCRI);};}
			);
	else $('#_autocomplete_DESCRI_div').fadeOut();
});
});