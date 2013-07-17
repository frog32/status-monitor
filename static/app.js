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
      if(data.direction == 'vertical'){
        this.$el.children().css('height', (100 / data.subwidgets.length)+ "%");
      } else {
        this.$el.children().css('width', (100 / data.subwidgets.length)+ "%");
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
    '<ul><% _.each( error_list, function( item ){ %>\
        <li>\
          <div class="count"><span><%= item.count %></span></div>\
          <h3><%- item.project %></h3>\
          <p><%= item.message %></p>\
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
    '<ul><% _.each( repositorys, function( item ){ %>\
        <li class="<%= item.last_build_state %>">\
          <h3><%- item.slug %> <span class="build-nr"><%= item.last_build_number %></span></h3>\
        </li>\
            <% }); %></ul>'
);


TravisWidget = WidgetBase.extend({
  repositorys:{},
  on_message: function(type, data){
    if(type == 'update'){
      this.repositorys[data["id"]] = data
      this.$el.html(JST['travis/repositorys']({repositorys:this.repositorys}));
    }
  }
});

status_monitor.register_widget_class('travis', TravisWidget);
