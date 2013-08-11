window.JST = {};

StatusMonitor = Backbone.View.extend({
  initialize: function(){
    this.sock = new SockJS('/ws/');
    this.sock.onopen = $.proxy(this.on_sock_open, this);
    this.sock.onclose = $.proxy(this.on_sock_close, this);
    this.sock.onmessage = $.proxy(this.on_sock_message, this);
    this.registry = {};
    this.widget_classes = {};
  },

  on_sock_open: function(){
    console.log('open');
  },

  on_sock_close: function(){
    console.log('close');
  },

  on_sock_message: function(message){
    console.log(message.data);
    if(message.data.target == 'sm'){
      this.on_message(message.data.type, message.data.data);
    } else {
      this.registry[message.data.target].on_message(message.data.type, message.data.data);
    }
  },

  on_message: function(type, data){
    if(type == 'create_root'){
      this.root = this.create_widget_instance(data.name, data.id);
    }
  },

  register_widget: function(widget){
    this.registry[widget.sm_id] = widget;
  },

  register_widget_class: function(name, widget_class){
    this.widget_classes[name] = widget_class;
  },

  create_widget_instance: function(name, sm_id){
    return new this.widget_classes[name]({el: $("#widget-" + sm_id), sm_id: sm_id}, this);
  }
});

var status_monitor = new StatusMonitor({ el: $("body") });

WidgetBase = Backbone.View.extend({
  initialize: function(options, sm){
    this.sm_id = options.sm_id;
    this.sm = sm;
    sm.register_widget(this);
  }
});

TextWidget = WidgetBase.extend({
  on_message: function(type, data){
    if(type == 'display'){
      this.$el.html( data.text );
    }
  }
});

status_monitor.register_widget_class('text', TextWidget);

SplitWidget = WidgetBase.extend({
  on_message: function(type, data){
    sm = this.sm;
    if(type == 'initialize'){
      data.subwidgets.forEach(function(subwidget){
        sm.create_widget_instance(subwidget.name, subwidget.id);
      });
      var property = (data.direction == 'vertical'? 'height': 'width');
      if(data.ratios){
        var i;
        for(i=0; i<data.ratios.length; i++){
          $(this.$el.children()[i]).css(property, data.ratios[i]);
        }
      } else {
        this.$el.children().css(property, (100 / data.subwidgets.length)+ "%");
      }
      if(data.direction != 'vertical'){
        this.$el.children().css('float', 'left');
      }
    }
  }
});

status_monitor.register_widget_class('split', SplitWidget);

ClockWidget = WidgetBase.extend({
  on_message: function(type, data){
    if(type == 'update'){
      this.$el.html(data.time);
    }
  }
});

status_monitor.register_widget_class('clock', ClockWidget);

// sentry

/*jshint multistr:true */
window.JST['sentry/errors'] = _.template(
    '<h2>Sentry</h2>\
    <ul><% _.each( error_list, function( item ){ %>\
        <li>\
          <div class="count"><%= item.count %></div>\
          <h3><%- item.project %></h3>\
          <div class="description"><%= item.message %></div>\
        </li>\
            <% }); %></ul>'
);


SentryWidget = WidgetBase.extend({
  on_message: function(type, data){
    if(type == 'update'){
      this.$el.html(JST['sentry/errors']({error_list:data}));
    }
  }
});

status_monitor.register_widget_class('sentry', SentryWidget);


window.JST['travis/repositorys'] = _.template(
    '<h2>Travis</h2>\
    <ul><% _.each( repositorys, function( item ){ %>\
        <li class="<%= item.last_build_state %>">\
          <h3><%- item.slug %> <span class="build-nr"><%= item.last_build_number %></span></h3>\
            <div class="description">\
              <span class="duration"><%- Math.floor(item.last_build_duration/60) %>min <%- item.last_build_duration%60 %>sec</span>\
              <span class="time"><% if(item.last_build_finished_at){ %><%= moment(item.last_build_finished_at).fromNow() %><% } %></span>\
          </div>\
        </li>\
      <% }); %>\
    </ul>'
);


TravisWidget = WidgetBase.extend({
  repositorys:{},
  timer: null,
  on_message: function(type, data){
    if(type == 'update'){
      this.repositorys[data["id"]] = data;
      if(this.timer === null){
        this.timer = window.setInterval($.proxy(this.render, this), 1000*30);
      }
      this.render();
    }
  },
  render: function(){
    this.$el.html(JST['travis/repositorys']({repositorys:this.repositorys}));
  }
});

status_monitor.register_widget_class('travis', TravisWidget);

window.JST['github/repos'] = _.template(
    '<h2>Github</h2>\
    <div>Public Repos <%- data.public_repos %></div>\
    <div>Private Repos <%- data.private_repos %></div>'
);

GithubWidget = WidgetBase.extend({
  on_message: function(type, data){
    if(type == 'update'){
      this.$el.html(JST['github/repos']({data: data}));
    }
  }
});

status_monitor.register_widget_class('github', GithubWidget);


window.JST['statuscake'] = _.template(
    '<h2>Up/Down</h2>\
    <div>Up <%- data.tests_up %></div>\
    <div>Down <%- data.tests_down %></div>\
    <div>Uptime <%- data.uptime %></div>\
    <ul><% _.each( data.failures, function( site ){ %>\
      <li><%- site.WebsiteName %></li>\
    <% }); %></ul>'
);

StatuscakeWidget = WidgetBase.extend({
  on_message: function(type, data){
    if(type == 'update'){
      this.$el.html(JST['statuscake']({data: data}));
    }
  }
});

status_monitor.register_widget_class('statuscake', StatuscakeWidget);
