webpackJsonp([0],{OBXJ:function(e,a,t){"use strict";var r=t("mtWM"),n=t.n(r),s=t("YaEn"),i=t("IcnI");a.a={name:"signup",data:function(){return{loader:!1,errorMessage:null,name:null,email:null,password:null,inviteCode:null}},methods:{signup:function(e){this.errorMessage=null;var a=this;e.preventDefault();n.a.post("/api/signup",{email:this.email,name:this.name,password:this.password,inviteCode:this.inviteCode}).then(function(e){var t=e.data.jwt,r=e.data.name,n=e.data.admin;null!==t&&null!==r&&null!==n?(localStorage.setItem("token",t),localStorage.setItem("name",r),localStorage.setItem("admin",n),i.a.commit("LOGIN_USER"),s.a.push("/")):a.errorMessage="Signup failed. Please try again."}).catch(function(e){if(e.response){var t=e.response.data;a.errorMessage=t.msg}a.errorMessage||(a.errorMessage=e.message),console.log(e)})}}}},psOb:function(e,a,t){"use strict";Object.defineProperty(a,"__esModule",{value:!0});var r=t("OBXJ"),n=t("zM9m"),s=t("VU/8"),i=s(r.a,n.a,!1,null,null,null);a.default=i.exports},zM9m:function(e,a,t){"use strict";var r=function(){var e=this,a=e.$createElement,t=e._self._c||a;return t("b-container",[t("b-card",{staticClass:"mx-auto",staticStyle:{"max-width":"23rem"},attrs:{header:"Sign up","border-variant":"secondary","header-border-variant":"secondary"}},[t("b-alert",{attrs:{show:!!e.errorMessage,dismissible:"",variant:"danger"}},[e._v(e._s(e.errorMessage))]),e._v(" "),t("b-form",{on:{submit:e.signup}},[t("b-form-group",{attrs:{label:"Name:","label-for":"signupEmail"}},[t("b-form-input",{attrs:{id:"signupEmail",type:"text",required:"",placeholder:"Enter name"},model:{value:e.name,callback:function(a){e.name=a},expression:"name"}})],1),e._v(" "),t("b-form-group",{attrs:{label:"Email:","label-for":"signupEmail"}},[t("b-form-input",{attrs:{id:"signupEmail",type:"email",required:"",placeholder:"Enter email"},model:{value:e.email,callback:function(a){e.email=a},expression:"email"}})],1),e._v(" "),t("b-form-group",{attrs:{label:"Password:","label-for":"signupPassword"}},[t("b-form-input",{attrs:{id:"signupPassword",type:"password",required:"",placeholder:"Enter password"},model:{value:e.password,callback:function(a){e.password=a},expression:"password"}})],1),e._v(" "),t("b-form-group",{attrs:{label:"Invite code:","label-for":"signupInviteCode"}},[t("b-form-input",{attrs:{id:"signupInviteCode",type:"inviteCode",required:"",placeholder:"Enter invite code"},model:{value:e.inviteCode,callback:function(a){e.inviteCode=a},expression:"inviteCode"}})],1),e._v(" "),t("b-row",{attrs:{"align-h":"end"}},[t("b-col",[t("b-link",{attrs:{"align-v":"center",to:"login"}},[e._v("Log in")])],1),e._v(" "),t("b-col",{attrs:{cols:"auto"}},[t("b-button",{attrs:{type:"submit",variant:"primary"}},[e._v("Sign up")]),e._v(" "),t("b-button",{attrs:{type:"reset",variant:"secondary"}},[e._v("Reset")])],1)],1)],1)],1)],1)},n=[],s={render:r,staticRenderFns:n};a.a=s}});
//# sourceMappingURL=0.417885cba67a407131eb.js.map