var WEB_ENV = 'production';
var CONFIG = {
  // 开发环境配置
  development: {
    assetsPath: '/static', // 静态资源路径
    baseUrl: 'https://jsgateway.zhixinst.com', // 后台接口请求地址
    hostUrl: 'https://jstest.zhixinst.com',             // 前端地址
    ssohost: 'https://sso.zxhnzq.com',
    baseUrlXxsy: 'https://xxsygateway.zxhnzq.com', // 后台接口请求地址
    classifyid: '15e1fdf7-ccec-47b1-8e9b-8ddf924158dd',
    kanbanUrl: 'https://chart.zhixinst.com/#/chart/preview/11',
    Realtime: true, //首页接口实时调用
    kind: 'csc2025',
    WebsiteType: '13',
    oldWebsit: 'https://2024csc.xxsuyang.com/',
	AIWebsit:'',
	aikey:'',
	// 军赛官网颜色配置
    junTheme: {
      primaryColor: '#a91013', // 主色调
      primaryColorHover: '#bc0f12', // 主色调悬停状态
      primaryColorLight: '#efdfe0' // 主色调浅色
    },
    // 通用官网颜色配置
    generalTheme: {
      primaryColor: '#1e67ca', // 通用主色调
      primaryColorHover: '#1557b0', // 通用主色调悬停状态
      primaryColorLight: '#e8f2ff' // 通用主色调浅色
    }
  },
  // 生产环境配置
  production: {
    assetsPath: '/static', // 静态资源路径
    baseUrl: 'https://jsgateway.zhixinst.com', // 后台接口请求地址
    hostUrl: 'https://js.zhixinst.com',             // 前端地址
    ssohost: 'https://sso.zxhnzq.com',
    baseUrlXxsy: 'https://jsgateway.zhixinst.com', // 后台接口请求地址
    classifyid: '584e1717-ed51-48fc-9195-72e3a87bbc88',
    kanbanUrl: 'https://chart.zhixinst.com/#/chart/preview/11,https://chart.zhixinst.com/#/chart/preview/13',
    Realtime: false, //首页接口实时调用
	showSf:true, //是否开启身份修改
	showApply:true,//是否开启学校报名
	cutTime:true,//时间轴倒计时
	showYuyue:false,
	menu: [false,false,false,false],
	filterDrovince: ['四川省','重庆市','浙江省','河南省'],
    kind: 'csc2025',
    WebsiteType: '13',
    oldWebsit: 'https://2024csc.xxsuyang.com/',
	AIWebsit:'https://jsgateway.zhixinst.com',
aikey:'3uGGfe9N6l',
lptjtd: true,
botid:'7510499427661381667',
batchid: ['8da1eb85-3e2a-4249-be3c-06df6f7e0c9a','afc1215f-3f81-44f2-9ebc-198fb0f78f74'],
yxzp: [
      {
        year:2025,
        type: "ppt",
        ids:["deb58b6d-4d69-49ae-9334-bdc480ff3477"]
      },
      {
        year:2024,
        type: "video",
        ids:["ed69dbab-23b6-475c-b04a-859342ae5201", "1632fde9-bd61-4fd0-bb4c-8d39cc608b06"]
      }
    ],
    cutTime: true,
    navLink: [
      {
        name: "中国知网",
        url: "/zhiwang",
        link: "",
        newBlank: true,
        islogin: true,
        children: [],
      },
      {
        name: "高校信息素养教育数据库",
        url: "xxsy",
        link: "https://xxsuyang.com/",
        islogin: false,
        children: [],
      },
      {
        name: "AI素养与技能提升数据库",
        url: "aisy",
        link: "https://ai.xxsuyang.com/",
        islogin: false,
        children: [],
      },
      {
        name: "爱思唯尔LeapSpace",
        url: "",
        link: "https://eci.elsevier.cn/resource/LeapSpace.html?fid=165&menuid=358&infoid=2004",
        islogin: true,
        children: [],
      },
    ],
	// 军赛官网颜色配置
    junTheme: {
      primaryColor: '#a91013', // 主色调
      primaryColorHover: '#bc0f12', // 主色调悬停状态
      primaryColorLight: '#efdfe0' // 主色调浅色
    },
    // 通用官网颜色配置
    generalTheme: {
      primaryColor: '#1e67ca', // 通用主色调
      primaryColorHover: '#1557b0', // 通用主色调悬停状态
      primaryColorLight: '#e8f2ff' // 通用主色调浅色
    }
  }
};
var WEBSITE_CONFIG = CONFIG[WEB_ENV];
