general = {

    showNotificationOwn: function(from, align, type, message, title = 'Visualiti SAS') {
        color = Math.floor((Math.random() * 4) + 1);

        $.notify({
            icon: "tim-icons icon-bell-55",
            message: message,
            title: title

        }, {
            type: type,
            timer: 8000,
            placement: {
                from: from,
                align: align
            }
        });
    },
    initDashboardPageCharts: function(canvaId, labels, data, labelLegeng = 'value') {

        gradientChartOptionsConfigurationWithTooltipPurple = {
            maintainAspectRatio: false,
            legend: {
                display: false
            },

            tooltips: {
                backgroundColor: '#f5f5f5',
                titleFontColor: '#333',
                bodyFontColor: '#666',
                bodySpacing: 4,
                xPadding: 12,
                mode: "nearest",
                intersect: 0,
                position: "nearest"
            },
            responsive: true,
            scales: {
                yAxes: [{
                    barPercentage: 1.6,
                    gridLines: {
                        drawBorder: false,
                        color: 'rgba(29,140,248,0.0)',
                        zeroLineColor: "transparent",
                    },
                    display: true
                }],

                xAxes: [{
                    barPercentage: 1.6,
                    gridLines: {
                        drawBorder: false,
                        color: 'rgba(225,78,202,0.1)',
                        zeroLineColor: "transparent",
                    },
                    ticks: {
                        padding: 1,
                        fontColor: "#9a9a9a"
                    }
                }]
            }
        };


        var chart_labels = labels;
        var chart_data = data;


        var ctx = document.getElementById(canvaId).getContext('2d');

        if (ctx.canvas.$chartjs != undefined) {
            eval("chart_" + canvaId + '.destroy();');
        }
        var gradientStroke = ctx.createLinearGradient(0, 230, 0, 50);

        gradientStroke.addColorStop(1, 'rgba(72,72,176,0.1)');
        gradientStroke.addColorStop(0.4, 'rgba(72,72,176,0.0)');
        gradientStroke.addColorStop(0, 'rgba(119,52,169,0)'); //purple colors
        var config = {
            type: 'line',
            data: {
                labels: chart_labels,
                datasets: [{
                    label: labelLegeng,
                    fill: true,
                    backgroundColor: gradientStroke,
                    borderColor: '#d346b1',
                    borderWidth: 2,
                    borderDash: [],
                    borderDashOffset: 0.0,
                    pointBackgroundColor: '#d346b1',
                    pointBorderColor: 'rgba(255,255,255,0)',
                    pointHoverBackgroundColor: '#d346b1',
                    pointBorderWidth: 1,
                    pointHoverRadius: 4,
                    pointHoverBorderWidth: 15,
                    pointRadius: 4,
                    data: chart_data,
                }]
            },
            options: gradientChartOptionsConfigurationWithTooltipPurple
        };
        eval("chart_" + canvaId + ' = new Chart(ctx, config)')


    }

};