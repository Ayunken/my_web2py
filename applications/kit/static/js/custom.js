/**
 * Created by julio on 2/1/17.
 Basic Usage:

$('#row_id').slideRow('down');
$('#row_id').slideRow('up');
Pass slide options as individual arguments:

$('#row_id').slideRow('down', 500); //slide speed
$('#row_id').slideRow('down', 500, function() { alert('Row available'); }); // slide speed and callback function
$('#row_id').slideRow('down', 500, 'linear', function() { alert('Row available'); }); slide speed, easing option and callback function
$('#row_id').slideRow('down', {slideSpeed: 500, easing: 'linear', callback: function() { alert('Row available');} }); //options passed as object
Basically, for the slide down animation, the plug-in wraps the contents of the cells in DIVs, animates those, then removes them, and vice versa for the slide up (with some extra steps to get rid of the cell padding). It also returns the object you called it on, so you can chain methods like so:

$('#row_id').slideRow('down').css({'font-color':'#F00'}); //make the text in the row red

 */
(function($) {
var sR = {
    defaults: {
        slideSpeed: 400,
        easing: false,
        callback: false
    },
    thisCallArgs: {
        slideSpeed: 400,
        easing: false,
        callback: false
    },
    methods: {
        up: function (arg1,arg2,arg3) {
            if(typeof arg1 == 'object') {
                for(p in arg1) {
                    sR.thisCallArgs.eval(p) = arg1[p];
                }
            }else if(typeof arg1 != 'undefined' && (typeof arg1 == 'number' || arg1 == 'slow' || arg1 == 'fast')) {
                sR.thisCallArgs.slideSpeed = arg1;
            }else{
                sR.thisCallArgs.slideSpeed = sR.defaults.slideSpeed;
            }

            if(typeof arg2 == 'string'){
                sR.thisCallArgs.easing = arg2;
            }else if(typeof arg2 == 'function'){
                sR.thisCallArgs.callback = arg2;
            }else if(typeof arg2 == 'undefined') {
                sR.thisCallArgs.easing = sR.defaults.easing;
            }
            if(typeof arg3 == 'function') {
                sR.thisCallArgs.callback = arg3;
            }else if(typeof arg3 == 'undefined' && typeof arg2 != 'function'){
                sR.thisCallArgs.callback = sR.defaults.callback;
            }
            var $cells = $(this).find('td');
            $cells.wrapInner('<div class="slideRowUp" />');
            var currentPadding = $cells.css('padding');
            $cellContentWrappers = $(this).find('.slideRowUp');
            $cellContentWrappers.slideUp(sR.thisCallArgs.slideSpeed,sR.thisCallArgs.easing).parent().animate({
                                                                                                                paddingTop: '0px',
                                                                                                                paddingBottom: '0px'},{
                                                                                                                complete: function () {
                                                                                                                    $(this).children('.slideRowUp').replaceWith($(this).children('.slideRowUp').contents());
                                                                                                                    $(this).parent().css({'display':'none'});
                                                                                                                    $(this).css({'padding': currentPadding});
                                                                                                                }});
            var wait = setInterval(function () {
                if($cellContentWrappers.is(':animated') === false) {
                    clearInterval(wait);
                    if(typeof sR.thisCallArgs.callback == 'function') {
                        sR.thisCallArgs.callback.call(this);
                    }
                }
            }, 100);
            return $(this);
        },
        down: function (arg1,arg2,arg3) {
            if(typeof arg1 == 'object') {
                for(p in arg1) {
                    sR.thisCallArgs.eval(p) = arg1[p];
                }
            }else if(typeof arg1 != 'undefined' && (typeof arg1 == 'number' || arg1 == 'slow' || arg1 == 'fast')) {
                sR.thisCallArgs.slideSpeed = arg1;
            }else{
                sR.thisCallArgs.slideSpeed = sR.defaults.slideSpeed;
            }

            if(typeof arg2 == 'string'){
                sR.thisCallArgs.easing = arg2;
            }else if(typeof arg2 == 'function'){
                sR.thisCallArgs.callback = arg2;
            }else if(typeof arg2 == 'undefined') {
                sR.thisCallArgs.easing = sR.defaults.easing;
            }
            if(typeof arg3 == 'function') {
                sR.thisCallArgs.callback = arg3;
            }else if(typeof arg3 == 'undefined' && typeof arg2 != 'function'){
                sR.thisCallArgs.callback = sR.defaults.callback;
            }
            var $cells = $(this).find('td');
            $cells.wrapInner('<div class="slideRowDown" style="display:none;" />');
            $cellContentWrappers = $cells.find('.slideRowDown');
            $(this).show();
            $cellContentWrappers.slideDown(sR.thisCallArgs.slideSpeed, sR.thisCallArgs.easing, function() { $(this).replaceWith( $(this).contents()); });

            var wait = setInterval(function () {
                if($cellContentWrappers.is(':animated') === false) {
                    clearInterval(wait);
                    if(typeof sR.thisCallArgs.callback == 'function') {
                        sR.thisCallArgs.callback.call(this);
                    }
                }
            }, 100);
            return $(this);
        },
        toggle: function(arg1,arg2,arg3){


        }
    }
};

$.fn.slideRow = function(method,arg1,arg2,arg3) {
    if(typeof method != 'undefined') {
        if (method=='toggle'){
            if ($(this).css('display')=='none')
                return sR.methods['down'].apply(this, Array.prototype.slice.call(arguments,1));
            else
                return sR.methods['up'].apply(this, Array.prototype.slice.call(arguments,1));
        }
        if(sR.methods[method]) {
            return sR.methods[method].apply(this, Array.prototype.slice.call(arguments,1));
        }
    }
};
})(jQuery);