general = {

    showNotificationOwn: function(from, align, type, message, title = 'Visualiti SAS', icon = "tim-icons icon-bell-55") {
        color = Math.floor((Math.random() * 4) + 1);

        $.notify({
            icon: icon,
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
    initLineCharts: function(canvaId, labels, data, labelLegeng = 'value', titleY = '', titleX = '') {

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
                    scaleLabel: {
                        display: true,
                        labelString: titleY
                    },
                    barPercentage: 1.6,
                    gridLines: {
                        drawBorder: false,
                        color: 'rgba(29,140,248,0.0)',
                        zeroLineColor: "transparent",
                    },
                    display: true
                }],

                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: titleX
                    },
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


    },
    initBarCharts: function(canvaId, labels, data, labelLegeng = 'value', titleY = '', titleX = '') {


        gradientBarChartConfiguration = {
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
                    scaleLabel: {
                        display: true,
                        labelString: titleY
                    },
                    gridLines: {
                        drawBorder: false,
                        color: 'rgba(29,140,248,0.1)',
                        zeroLineColor: "transparent",
                    },
                    ticks: {
                        suggestedMin: 60,
                        suggestedMax: 120,
                        padding: 20,
                        fontColor: "#9e9e9e"
                    }
                }],

                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: titleX
                    },
                    gridLines: {
                        drawBorder: false,
                        color: 'rgba(29,140,248,0.1)',
                        zeroLineColor: "transparent",
                    },
                    ticks: {
                        padding: 20,
                        fontColor: "#9e9e9e"
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

        gradientStroke.addColorStop(1, 'rgba(66,134,121,0.15)');
        gradientStroke.addColorStop(0.4, 'rgba(66,134,121,0.0)'); //green colors
        gradientStroke.addColorStop(0, 'rgba(66,134,121,0)'); //green colors
        var config = {
            type: 'bar',
            data: {
                labels: chart_labels,
                datasets: [{
                    label: labelLegeng,
                    fill: true,
                    backgroundColor: gradientStroke,
                    borderColor: '#00d6b4',
                    borderWidth: 2,
                    borderDash: [],
                    borderDashOffset: 0.0,
                    pointBackgroundColor: '#00d6b4',
                    pointBorderColor: 'rgba(255,255,255,0)',
                    pointHoverBackgroundColor: '#00d6b4',
                    pointBorderWidth: 1,
                    pointHoverRadius: 4,
                    pointHoverBorderWidth: 15,
                    pointRadius: 4,
                    data: chart_data,
                }]
            },
            options: gradientBarChartConfiguration
        };
        eval("chart_" + canvaId + ' = new Chart(ctx, config)')


    },
    initMultipleAxesHighCharts: function(idDiv, labels, data, medidas = [], sensores = [], titleY = '', titleX = '', tipo = 'spline', plotBand = null, plotBandRepet = false) {
        function toNumber(value) {
            return Number(value);
        }
        varSeries = [];
        yAxises = [];
        i = 0;
        opposite = false;
        data.forEach(dato => {
            tipoBarra = tipo;
            if (sensores.at(i).localeCompare("precipitación") === 0 || sensores.at(i).localeCompare("Precipitación") === 0 || sensores.at(i).localeCompare("precipitacion") === 0) {
                tipoBarra = 'column';
            }
            var serie = {
                name: sensores.at(i),
                type: tipoBarra,
                yAxis: i,
                data: dato.map(toNumber),
                marker: {
                    enabled: false
                },
                dashStyle: 'shortdot',
                tooltip: {
                    valueSuffix: ' ' + medidas.at(i)
                }

            };
            varSeries.push(serie);

            if (plotBand != null && plotBand.length > 0) {
                titlePlotBand = {
                    marker: {
                        symbol: 'square',
                        radius: 4
                    },
                    type: 'scatter',
                    plotBandsIndex: 0,
                    name: 'PMP (Punto de Marchitez Permanente)',
                    color: 'rgba(255, 0, 0, 0.2)'
                };
                varSeries.push(titlePlotBand);
                titlePlotBand = {
                    marker: {
                        symbol: 'square',
                        radius: 4
                    },
                    type: 'scatter',
                    plotBandsIndex: 1,
                    name: 'CC (Capacidad de Campo)',
                    color: 'rgba(0, 150, 50, 0.2)'
                };
                varSeries.push(titlePlotBand);
                titlePlotBand = {
                    marker: {
                        symbol: 'square',
                        radius: 4
                    },
                    type: 'scatter',
                    plotBandsIndex: 2,
                    name: 'Exceso Hídrico',
                    color: 'rgba(0, 0, 255, 0.2)'
                };
                varSeries.push(titlePlotBand);
            }


            var yAxis = { // Primary yAxis
                gridLineWidth: 0,
                title: {
                    text: sensores.at(i),
                    style: {
                        color: Highcharts.getOptions().colors[i]
                    }
                },
                labels: {
                    format: '{value}' + medidas.at(i).substr(medidas.at(i).indexOf("(") + 1).replace(')', ''),
                    style: {
                        color: Highcharts.getOptions().colors[i]
                    }
                },
                plotBands: plotBand,
                opposite: opposite

            };
            yAxises.push(yAxis);

            opposite = !opposite;
            if (!plotBandRepet) {
                plotBand = null;
            }
            i++;

        });

        // var data = data.map(toNumber)
        Highcharts.chart(idDiv, {
            chart: {
                zoomType: 'xy'
            },
            title: {
                text: titleY,
                align: 'left',
                style: {
                    color: '#00efc4'

                }
            },
            // subtitle: {
            //     text: 'Source: WorldClimate.com',
            //     align: 'left'
            // },
            xAxis: [{
                categories: labels,
                labels: {
                    style: {
                        color: '#00efc4'

                    }
                },
                crosshair: true
            }],
            yAxis: yAxises,
            tooltip: {
                shared: true
            },
            legend: {
                layout: 'vertical',
                align: 'left',
                x: 80,
                verticalAlign: 'top',
                y: 55,
                floating: true,
                backgroundColor: Highcharts.defaultOptions.legend.backgroundColor || // theme
                    'rgba(255,255,255,0.25)'
            },
            plotOptions: {
                spline: {
                    marker: {
                        radius: 4,
                        lineWidth: 1
                    }
                },
                series: {
                    allowPointSelect: false,
                    events: {
                        legendItemClick: function() {
                            var newPlotBands = [],
                                yAxis = this.chart.yAxis[0],
                                plotBandsIndex;

                            if (Highcharts.isNumber(this.options.plotBandsIndex)) {
                                this.chart.series.forEach(function(s) {
                                    plotBandsIndex = s.options.plotBandsIndex;

                                    if (this !== s && Highcharts.isNumber(plotBandsIndex)) {
                                        if (s.visible) {
                                            newPlotBands.push(plotBand[plotBandsIndex])
                                        }
                                    } else if (this === s && !s.visible) {
                                        newPlotBands.push(plotBand[plotBandsIndex])
                                    }
                                }, this);

                                yAxis.update({
                                    plotBands: newPlotBands
                                });
                            }
                        }
                    }
                }
            },
            series: varSeries,
            responsive: {
                rules: [{
                    condition: {
                        maxWidth: 500
                    },
                    chartOptions: {
                        legend: {
                            floating: false,
                            layout: 'horizontal',
                            align: 'center',
                            verticalAlign: 'bottom',
                            x: 0,
                            y: 0
                        },
                        yAxis: [{
                            labels: {
                                align: 'right',
                                x: 0,
                                y: -6
                            },
                            showLastLabel: false
                        }, {
                            labels: {
                                align: 'left',
                                x: 0,
                                y: -6
                            },
                            showLastLabel: false
                        }, {
                            visible: false
                        }]
                    }
                }]
            }
        });

    },
    rangeDatePicker(div, input, maxToday = false) {
        var date = new Date();
        var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
        var maxDate = (maxToday) ? (date.getMonth() + 1) + "/" + (date.getDate()) + "/" + date.getFullYear() : '01/01/3000';

        $('#' + div).daterangepicker({
            format: 'DD/MM/YYYY',
            startDate: firstDay,
            endDate: lastDay,
            minDate: '01/01/2015',
            maxDate: maxDate,
            showDropdowns: true,
            timePicker: false,
            buttonClasses: ['btn', 'btn-sm'],
            applyClass: 'btn-success btn-outline btn-sm',
            cancelClass: 'btn-warning btn-outline btn-sm',
            locale: {
                applyLabel: 'Aceptar',
                cancelLabel: 'Cancelar',
                daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
                monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
                firstDay: 1
            }
        }, function(start, end, label) {
            $('#' + input).val(start.format('DD/MM/YYYY') + ' - ' + end.format('DD/MM/YYYY'));
        });

        $('#' + input).val((moment().startOf('month').format('DD/MM/YYYY')) + ' - ' + (moment().format('DD/MM/YYYY')));
    },
    obtenerFrm(div) {
        return $("#" + div).serializeArray().reduce(function(obj, item) {
            obj[item.name] = item.value;
            return obj;
        }, {});
    }

};