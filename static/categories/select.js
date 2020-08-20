window.addEventListener("load", function () {
    (function ($) {
        function custom_template(obj) {
            var text = $(obj.element).text();
            var data = $(obj.element).data();

            if (data && data["src"]) {
                var imgSrc = data["src"];

                template = $(
                    '<span style="display:inline-flex;align-items:center;"><img src="' +
                        imgSrc +
                        '" style="width:24px;height:24px;margin-right:10px;"/>' +
                        text +
                        "</span>"
                );

                return template;
            }
        }

        var options = {
            templateSelection: custom_template,
            templateResult: custom_template,
            minimumResultsForSearch: -1,
        };

        $("#id_icon").select2(options);
        $(".select2-container").css({
            width: "200px",
        });
    })(django.jQuery);
});
