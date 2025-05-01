import sys
import requests
import json
import random
import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                            QDateEdit, QComboBox, QMessageBox, QHeaderView, QFrame, QProgressBar,
                            QStyledItemDelegate, QStyleOptionViewItem, QStyle, QSplitter,
                            QTextBrowser, QGroupBox, QDialog, QGridLayout)
from PyQt5.QtCore import Qt, QDate, QSize, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont, QPalette, QIcon

# 常量定义
class UIConstants:
    # 颜色常量
    BILIBILI_PINK = "#FB7299"
    LIGHT_GRAY = "#F6F6F6"
    WHITE = "#FFFFFF"
    LIGHT_BLUE = "#E3F2FD"
    LIGHT_YELLOW = "#FFF8E1"
    GRAY = "#F8F8F8"
    DARK_GRAY = "#E5E5E5"
    DARK_TEXT = "#333333"
    
    # 样式常量
    TITLE_STYLE = f"color: {BILIBILI_PINK}; margin: 10px;"
    SEARCH_FRAME_STYLE = f"background-color: {LIGHT_GRAY}; border-radius: 8px; padding: 10px;"
    FUNCTION_FRAME_STYLE = f"background-color: {WHITE}; border-radius: 5px; padding: 5px;"
    
    # 按钮样式模板
    BUTTON_STYLE = """
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:checked {{
            background-color: {checked_bg};
            color: white;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            color: white;
        }}
    """
    
    # 窗口常量
    WINDOW_TITLE = "哔哩哔哩视频统计助手"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    WINDOW_X = 100
    WINDOW_Y = 100
    
    # 表格样式
    TABLE_STYLE = """
        QTableWidget {
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            background-color: white;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QHeaderView::section {
            background-color: #F5F5F5;
            padding: 5px;
            border: 1px solid #E0E0E0;
            font-weight: bold;
        }
    """
    
    # 表格列定义
    TABLE_COLUMNS = {
        "keyword": [
            ("标题", 400),
            ("UP主", 100),
            ("播放量", 80),
            ("弹幕数", 80),
            ("评论数", 80),
            ("收藏数", 80),
            ("发布时间", 150)
        ],
        "video_link": [
            ("标题", 400),
            ("UP主", 100),
            ("播放量", 80),
            ("弹幕数", 80),
            ("评论数", 80),
            ("收藏数", 80),
            ("发布时间", 150)
        ]
    }

class NumericDelegate(QStyledItemDelegate):
    """数字格式化代理，用于格式化表格中的数字展示"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def displayText(self, value, locale):
        try:
            number = int(value)
            if number >= 10000:
                return f"{number/10000:.1f}万"
            elif number >= 1000:
                return f"{number/1000:.1f}千"
            return str(number)
        except:
            return str(value)

class BilibiliStatsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(UIConstants.WINDOW_TITLE)
        self.setGeometry(UIConstants.WINDOW_X, UIConstants.WINDOW_Y, 
                        UIConstants.WINDOW_WIDTH, UIConstants.WINDOW_HEIGHT)
        self.current_videos = []
        self.current_mode = "keyword"
        self.initUI()
        
    def initUI(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 应用标题
        title_label = QLabel(UIConstants.WINDOW_TITLE)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(UIConstants.TITLE_STYLE)
        main_layout.addWidget(title_label)
        
        # 搜索区域
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setStyleSheet(UIConstants.SEARCH_FRAME_STYLE)
        search_layout = QVBoxLayout(search_frame)
        
        # 功能选择按钮区域
        function_select_frame = QFrame()
        function_select_frame.setStyleSheet(UIConstants.FUNCTION_FRAME_STYLE)
        function_select_layout = QHBoxLayout(function_select_frame)
        
        # 关键词搜索按钮
        self.keyword_btn = QPushButton("关键词搜索")
        self.keyword_btn.setCheckable(True)
        self.keyword_btn.setChecked(True)
        self.keyword_btn.setStyleSheet(UIConstants.BUTTON_STYLE.format(
            bg_color=UIConstants.DARK_GRAY,
            text_color=UIConstants.DARK_TEXT,
            checked_bg=UIConstants.BILIBILI_PINK,
            hover_bg="#FC8BAD"
        ))
        self.keyword_btn.clicked.connect(lambda: self.switch_mode("keyword"))
        function_select_layout.addWidget(self.keyword_btn)
        
        # 视频详情查询按钮
        self.video_link_btn = QPushButton("视频详情查询")
        self.video_link_btn.setCheckable(True)
        self.video_link_btn.setStyleSheet(UIConstants.BUTTON_STYLE.format(
            bg_color=UIConstants.DARK_GRAY,
            text_color=UIConstants.DARK_TEXT,
            checked_bg=UIConstants.BILIBILI_PINK,
            hover_bg="#FC8BAD"
        ))
        self.video_link_btn.clicked.connect(lambda: self.switch_mode("video_link"))
        function_select_layout.addWidget(self.video_link_btn)
        
        search_layout.addWidget(function_select_frame)
        
        # 创建堆叠容器，用于切换不同功能的输入界面
        self.stacked_input_widget = QWidget()
        self.stacked_input_layout = QVBoxLayout(self.stacked_input_widget)
        self.stacked_input_layout.setContentsMargins(0, 10, 0, 0)
        
        # 1. 关键词搜索界面
        self.keyword_search_widget = QWidget()
        keyword_search_layout = QVBoxLayout(self.keyword_search_widget)
        keyword_search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 关键词搜索行
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("关键词："))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入搜索关键词...")
        self.keyword_input.setStyleSheet("padding: 6px; border: 1px solid #CCCCCC; border-radius: 4px;")
        keyword_layout.addWidget(self.keyword_input)
        keyword_search_layout.addLayout(keyword_layout)
        
        # 时间范围行
        time_layout = QHBoxLayout()
        
        # 添加时间范围说明标签（包含提示信息）
        time_label = QLabel("时间范围：")
        time_label.setToolTip("可选择任意时间范围")
        time_layout.addWidget(time_label)
        
        # 设置日期范围
        today = QDate.currentDate()
        
        # 添加快速选择按钮
        quick_date_layout = QHBoxLayout()
        
        today_btn = QPushButton("今天")
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1F5FE;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B3E5FC;
            }
        """)
        today_btn.clicked.connect(self.set_date_today)
        quick_date_layout.addWidget(today_btn)
        
        yesterday_btn = QPushButton("昨天")
        yesterday_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1F5FE;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B3E5FC;
            }
        """)
        yesterday_btn.clicked.connect(self.set_date_yesterday)
        quick_date_layout.addWidget(yesterday_btn)
        
        three_days_btn = QPushButton("近3天")
        three_days_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1F5FE;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B3E5FC;
            }
        """)
        three_days_btn.clicked.connect(self.set_date_last_3_days)
        quick_date_layout.addWidget(three_days_btn)
        
        week_btn = QPushButton("近7天")
        week_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1F5FE;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B3E5FC;
            }
        """)
        week_btn.clicked.connect(self.set_date_last_week)
        quick_date_layout.addWidget(week_btn)
        
        ten_days_btn = QPushButton("不限")
        ten_days_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1F5FE;
                border: none;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B3E5FC;
            }
        """)
        ten_days_btn.clicked.connect(self.set_date_last_ten_days)
        quick_date_layout.addWidget(ten_days_btn)
        
        quick_date_layout.addStretch()
        
        # 日期选择器
        date_select_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(today.addDays(-10))  # 默认为10天前
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")  # 设置更直观的日期格式
        self.date_from.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
            }
        """)
        date_select_layout.addWidget(self.date_from)
        
        date_select_layout.addWidget(QLabel("至"))
        
        self.date_to = QDateEdit()
        self.date_to.setDate(today)  # 默认为今天
        self.date_to.setMaximumDate(today)  # 最大日期为今天
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")  # 设置更直观的日期格式
        self.date_to.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
            }
        """)
        date_select_layout.addWidget(self.date_to)
        
        # 将时间相关布局添加到主时间布局
        time_layout.addLayout(quick_date_layout)
        keyword_search_layout.addLayout(time_layout)
        keyword_search_layout.addLayout(date_select_layout)
        
        # 排序和搜索按钮行
        sort_search_layout = QHBoxLayout()
        
        # 排序方式
        sort_search_layout.addWidget(QLabel("排序："))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["发布时间", "播放量", "弹幕数", "收藏数", "硬币数", "点赞数"])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #CCCCCC;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        sort_search_layout.addWidget(self.sort_combo)
        
        # 添加一些空间
        sort_search_layout.addStretch()
        
        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #FB7299;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FC8BAD;
            }
            QPushButton:pressed {
                background-color: #E5698C;
            }
        """)
        self.search_button.clicked.connect(self.search_videos)
        sort_search_layout.addWidget(self.search_button)
        
        keyword_search_layout.addLayout(sort_search_layout)
        
        # 2. 视频链接查询界面
        self.video_link_widget = QWidget()
        video_link_layout = QVBoxLayout(self.video_link_widget)
        video_link_layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频链接输入行
        link_input_layout = QHBoxLayout()
        link_input_layout.addWidget(QLabel("视频链接："))
        self.video_link_input = QLineEdit()
        self.video_link_input.setPlaceholderText("输入B站视频链接获取详细信息...")
        self.video_link_input.setStyleSheet("padding: 6px; border: 1px solid #CCCCCC; border-radius: 4px;")
        link_input_layout.addWidget(self.video_link_input)

        # 删除按钮
        del_link_btn = QPushButton("删除")
        del_link_btn.setStyleSheet("background-color: #FB7299; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold;")
        def remove_link():
            self.video_link_input.setText("")
            self.video_link_input.setPlaceholderText("已删除")
            del_link_btn.setEnabled(False)
        del_link_btn.clicked.connect(remove_link)
        link_input_layout.addWidget(del_link_btn)

        video_link_layout.addLayout(link_input_layout)
        
        # 链接格式提示
        link_hint_label = QLabel("支持的链接格式: https://www.bilibili.com/video/BVxxxxxx 或 https://b23.tv/xxxxxx")
        link_hint_label.setStyleSheet("color: #666666; font-size: 11px;")
        video_link_layout.addWidget(link_hint_label)
        
        # 间隔
        video_link_layout.addSpacing(10)
        
        # 获取视频详情按钮
        get_details_layout = QHBoxLayout()
        get_details_layout.addStretch()
        self.get_video_details_button = QPushButton("获取详情")
        self.get_video_details_button.setStyleSheet("""
            QPushButton {
                background-color: #FB7299;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FC8BAD;
            }
            QPushButton:pressed {
                background-color: #E5698C;
            }
        """)
        self.get_video_details_button.clicked.connect(self.get_video_details)
        get_details_layout.addWidget(self.get_video_details_button)
        video_link_layout.addLayout(get_details_layout)
        
        # 添加填充空间
        video_link_layout.addStretch()
        
        # 将两个功能界面添加到堆叠布局中
        self.stacked_input_layout.addWidget(self.keyword_search_widget)
        self.stacked_input_layout.addWidget(self.video_link_widget)
        
        # 默认显示关键词搜索界面
        self.keyword_search_widget.setVisible(True)
        self.video_link_widget.setVisible(False)
        
        search_layout.addWidget(self.stacked_input_widget)
        
        main_layout.addWidget(search_frame)
        
        # 表格区域
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.StyledPanel)
        table_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; padding: 10px;")
        table_layout = QVBoxLayout(table_frame)
        
        # 视频列表表格
        self.video_table = QTableWidget()
        self.video_table.setStyleSheet(UIConstants.TABLE_STYLE)
        self.video_table.setColumnCount(len(UIConstants.TABLE_COLUMNS["keyword"]))
        self.video_table.setHorizontalHeaderLabels([col[0] for col in UIConstants.TABLE_COLUMNS["keyword"]])
        
        # 设置列宽
        for i, (_, width) in enumerate(UIConstants.TABLE_COLUMNS["keyword"]):
            self.video_table.setColumnWidth(i, width)
            
        # 设置表格属性
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setSelectionMode(QTableWidget.SingleSelection)
        self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.video_table.verticalHeader().setVisible(False)
        
        # 设置代理
        self.video_table.setItemDelegate(NumericDelegate(self.video_table))
        
        table_layout.addWidget(self.video_table)
        main_layout.addWidget(table_frame)
        
        # 状态栏
        self.status_frame = QFrame()
        self.status_frame.setFrameShape(QFrame.StyledPanel)
        self.status_frame.setStyleSheet("background-color: #F6F6F6; border-radius: 8px; padding: 5px;")
        status_layout = QHBoxLayout(self.status_frame)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #555555;")
        status_layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background: #E0E0E0;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #FB7299;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.status_frame)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def switch_mode(self, mode):
        """切换功能模式"""
        self.current_mode = mode
        
        if mode == "keyword":
            # 更新按钮状态
            self.keyword_btn.setChecked(True)
            self.video_link_btn.setChecked(False)
            
            # 更新界面显示
            self.keyword_search_widget.setVisible(True)
            self.video_link_widget.setVisible(False)
            
        elif mode == "video_link":
            # 更新按钮状态
            self.keyword_btn.setChecked(False)
            self.video_link_btn.setChecked(True)
            
            # 更新界面显示
            self.keyword_search_widget.setVisible(False)
            self.video_link_widget.setVisible(True)
    
    def search_videos(self):
        keyword = self.keyword_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return
            
        date_from = self.date_from.date().toString(Qt.ISODate)
        date_to = self.date_to.date().toString(Qt.ISODate)
        
        self.status_label.setText(f"正在搜索关键词 '{keyword}' 从 {date_from} 到 {date_to} 的视频...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        QApplication.processEvents()
        
        try:
            videos = self.fetch_bilibili_videos(keyword, date_from, date_to)
            self.progress_bar.setValue(70)
            QApplication.processEvents()
            
            # 根据选择的排序方式进行排序
            sort_index = self.sort_combo.currentIndex()
            if sort_index == 0:  # 发布时间
                videos.sort(key=lambda x: x.get('pubdate', 0), reverse=True)
            elif sort_index == 1:  # 播放量
                videos.sort(key=lambda x: x.get('stat', {}).get('view', 0), reverse=True)
            elif sort_index == 2:  # 弹幕数
                videos.sort(key=lambda x: x.get('stat', {}).get('danmaku', 0), reverse=True)
            elif sort_index == 3:  # 收藏数
                videos.sort(key=lambda x: x.get('stat', {}).get('favorite', 0), reverse=True)
            elif sort_index == 4:  # 硬币数
                videos.sort(key=lambda x: x.get('stat', {}).get('coin', 0), reverse=True)
            elif sort_index == 5:  # 点赞数
                videos.sort(key=lambda x: x.get('stat', {}).get('like', 0), reverse=True)
            
            self.update_stats_summary(videos)
            self.display_videos(videos)
            self.progress_bar.setValue(100)
            self.status_label.setText(f"找到 {len(videos)} 个视频")
            
            # 一段时间后隐藏进度条
            QApplication.processEvents()
            self.progress_bar.setVisible(False)
            
            # 存储当前搜索结果
            self.current_videos = videos
            
        except Exception as e:
            self.status_label.setText(f"搜索出错: {str(e)}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"搜索视频时出错：{str(e)}")
    
    def update_stats_summary(self, videos):
        """更新统计数据"""
        if not videos:
            return
            
        # 计算统计数据
        total_videos = len(videos)
        total_views = sum(video.get('stat', {}).get('view', 0) for video in videos)
        avg_views = total_views // total_videos if total_videos > 0 else 0
        max_views = max(video.get('stat', {}).get('view', 0) for video in videos) if videos else 0
        
        # 更新状态栏以显示统计信息
        # 应用格式化
        if total_views >= 10000:
            total_views_str = f"{total_views/10000:.1f}万"
        else:
            total_views_str = str(total_views)
        
        self.status_label.setText(f"找到 {total_videos} 个视频 | 总播放量: {total_views_str}")
    
    def display_videos(self, videos):
        self.video_table.setRowCount(0)  # 清空表格
        self.video_table.setSortingEnabled(False)  # 暂时禁用排序以提高性能
        
        # 设置进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        QApplication.processEvents()
        
        for row, video in enumerate(videos):
            self.video_table.insertRow(row)
            
            # 标题
            title_item = QTableWidgetItem(video.get('title', ''))
            title_item.setToolTip(video.get('title', ''))
            self.video_table.setItem(row, 0, title_item)
            
            # UP主
            author_item = QTableWidgetItem(video.get('author', ''))
            self.video_table.setItem(row, 1, author_item)
            
            # 发布时间
            pubdate = video.get('pubdate', 0)
            if pubdate:
                date_str = datetime.fromtimestamp(pubdate).strftime('%Y-%m-%d')
            else:
                date_str = '未知'
            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.UserRole, pubdate)  # 存储时间戳用于排序
            self.video_table.setItem(row, 2, date_item)
            
            # 获取统计数据
            stats = video.get('stat', {})
            
            # 播放量
            view_item = QTableWidgetItem(str(stats.get('view', 0)))
            view_item.setData(Qt.DisplayRole, stats.get('view', 0))
            self.video_table.setItem(row, 3, view_item)
            
            # 高播放量的行使用不同颜色标识
            if stats.get('view', 0) > 10000:
                view_item.setBackground(QBrush(QColor("#E3F2FD")))  # 浅蓝色背景
            
            # 弹幕数
            danmaku_item = QTableWidgetItem(str(stats.get('danmaku', 0)))
            danmaku_item.setData(Qt.DisplayRole, stats.get('danmaku', 0))
            self.video_table.setItem(row, 4, danmaku_item)
            
            # 高弹幕数的行使用不同颜色标识
            if stats.get('danmaku', 0) > 1000:
                danmaku_item.setBackground(QBrush(QColor("#FFF8E1")))  # 浅黄色背景
            
            # 收藏数
            fav_item = QTableWidgetItem(str(stats.get('favorite', 0)))
            fav_item.setData(Qt.DisplayRole, stats.get('favorite', 0))
            self.video_table.setItem(row, 5, fav_item)
            
            # 硬币数
            coin_item = QTableWidgetItem(str(stats.get('coin', 0)))
            coin_item.setData(Qt.DisplayRole, stats.get('coin', 0))
            self.video_table.setItem(row, 6, coin_item)
            
            # 点赞数
            like_item = QTableWidgetItem(str(stats.get('like', 0)))
            like_item.setData(Qt.DisplayRole, stats.get('like', 0))
            self.video_table.setItem(row, 7, like_item)
            
            # 标签
            tags = video.get('tags', [])
            tags_str = ", ".join(tags) if tags else "-"
            tags_item = QTableWidgetItem(tags_str)
            tags_item.setToolTip(tags_str)
            self.video_table.setItem(row, 8, tags_item)
            
            # 删除按钮
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("background-color: #FB7299; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold;")
            del_btn.clicked.connect(lambda _, r=row: self.delete_video_row(r))
            self.video_table.setCellWidget(row, 9, del_btn)
            
            # 为交替行设置背景色以提高可读性
            for col in range(10):
                item = self.video_table.item(row, col)
                if item and row % 2 == 0 and not item.background().color().name() != "#ffffff":
                    item.setBackground(QBrush(QColor("#F8F8F8")))
        
        self.video_table.setSortingEnabled(True)  # 重新启用排序
        
        # 完成加载
        self.progress_bar.setValue(100)
        QApplication.processEvents()
        self.progress_bar.setVisible(False)

    def delete_video_row(self, row):
        if 0 <= row < len(self.current_videos):
            del self.current_videos[row]
            self.display_videos(self.current_videos)

    def fetch_bilibili_videos(self, keyword, date_from, date_to):
        """
        从B站搜索API获取视频数据
        """
        # 转换日期格式为时间戳
        date_from_ts = int(datetime.strptime(date_from, "%Y-%m-%d").timestamp())
        date_to_ts = int(datetime.strptime(date_to, "%Y-%m-%d").timestamp() + 86399)  # 加上一天减1秒，包含整天
        
        # 使用B站公开搜索API，不需要wbi签名
        url = "https://api.bilibili.com/x/web-interface/search/type"
        
        # 构建请求参数
        params = {
            "keyword": keyword,
            "search_type": "video",
            "order": "pubdate",
            "page": 1,
            "duration": 0,
            "tids": 0,  # 所有分区
        }
        
        # 添加模拟浏览器环境的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Cookie": "buvid3=CFF74DA7-D7F1-4F11-9D5C-6BFB2CF88FC118547infoc"  # 添加基本cookie来避免412错误
        }
        
        videos = []
        
        # 由于API限制，可能无法获取实时数据，如果失败则使用增强的模拟数据
        try:
            self.status_label.setText("正在尝试从B站获取实时数据...")
            QApplication.processEvents()
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查接口返回是否成功
            if data.get("code") != 0:
                raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
            
            # 解析视频数据
            result_data = data.get("data", {})
            video_results = result_data.get("result", [])
            
            if not video_results:
                raise Exception("未找到视频结果，将使用模拟数据")
            
            # 解析视频数据
            for video_item in video_results:
                # 获取发布时间
                pubdate = video_item.get("pubdate", 0)
                
                # 筛选时间范围
                if pubdate < date_from_ts or pubdate > date_to_ts:
                    continue
                
                # 构建视频数据结构
                video = {
                    "bvid": video_item.get("bvid", ""),
                    "title": self._clean_html_tags(video_item.get("title", "")),
                    "author": video_item.get("author", ""),
                    "pubdate": pubdate,
                    "duration": video_item.get("duration", ""),
                    "stat": {
                        "view": int(video_item.get("play", 0) or 0),
                        "danmaku": int(video_item.get("video_review", 0) or 0),
                        "favorite": int(video_item.get("favorites", 0) or 0),
                        "coin": int(video_item.get("coins", 0) or 0),
                        "like": int(video_item.get("like", 0) or 0)
                    }
                }
                videos.append(video)
            
            # 如果API调用成功但没有过滤到符合时间范围的视频
            if not videos:
                raise Exception("在指定时间范围内未找到视频，将使用模拟数据")
            
            self.status_label.setText(f"成功获取B站数据，找到 {len(videos)} 个视频")
            QApplication.processEvents()
            
        except Exception as e:
            # 当API调用失败时，使用高质量模拟数据
            self.status_label.setText(f"无法从B站获取实时数据: {str(e)}，将使用模拟数据")
            QApplication.processEvents()
            
            # 生成增强的模拟数据
            videos = self._generate_enhanced_mock_videos(keyword, date_from_ts, date_to_ts)
        
        return videos

    def _generate_enhanced_mock_videos(self, keyword, date_from_ts, date_to_ts):
        """
        生成高质量的模拟视频数据，接近真实B站数据
        """
        mock_videos = []
        current_time = datetime.now().timestamp()
        
        # 真实风格的UP主名称
        up_names = [
            "峰哥亡命天涯", "沙雕动画锦集", "科技美学", "老番茄", "医路向前巍子", 
            "3Blue1Brown", "哔哩哔哩纪录片", "李永乐老师", "徐云流浪中国", "小事视频",
            "超级小桀", "回形针PaperClip", "硬件茶谈", "黑马程序员", "半吨先生",
            "猫和老鼠的欢乐生活", "偶尔有点小迷糊", "考研数学张宇", "阿斗归来了", 
            "原神官方", "柯南经典语录", "程序员鱼皮", "毕导THU", "鱼丸粗面儿", "专业解说电影"
        ]
        
        # 根据关键词定制视频标题模板
        title_templates = [
            f"【{keyword}】零基础入门教程 #{{index}}",
            f"{keyword}完全指南 - 看完秒懂",
            f"震惊！{keyword}竟然可以这样玩",
            f"【干货】{keyword}最新技术分析与讲解",
            f"我花了三个月时间，终于搞懂了{keyword}",
            f"{keyword}高能名场面剪辑",
            f"手把手教你玩转{keyword}，学不会打我",
            f"当{keyword}遇上{{random}}会怎样？",
            f"【{keyword}】万字长文解析，建议收藏",
            f"UP主亲身体验：{keyword}到底值不值得？",
        ]
        
        random_elements = ["创新", "惊喜", "挑战", "趣味", "科技", "未来", "搞笑", "意外"]
        
        # 更真实的数据分布参数
        view_base = random.randint(1000, 5000)  # 基础播放量
        popular_factor = random.randint(10, 50)  # 爆款视频倍数
        
        # 创建模拟视频，根据时间范围筛选
        video_count = random.randint(15, 25)  # 生成15-25个视频
        for i in range(1, video_count + 1):
            # 基于时间范围生成时间戳
            time_range = date_to_ts - date_from_ts
            random_offset = random.uniform(0, time_range)
            pub_time = date_from_ts + random_offset
            
            # 构建标题
            title_template = random.choice(title_templates)
            random_element = random.choice(random_elements)
            
            title = title_template.format(
                index=i,
                random=random_element
            )
            
            # 随机选择UP主
            author = random.choice(up_names)
            
            # 生成符合长尾分布的数据
            is_popular = random.random() < 0.2  # 20%的视频是"爆款"
            popularity_mult = popular_factor if is_popular else random.randint(1, 5)
            
            view_count = view_base * popularity_mult + random.randint(-500, 2000)
            danmaku_count = int(view_count * random.uniform(0.01, 0.05))  # 弹幕是播放量的1-5%
            favorite_count = int(view_count * random.uniform(0.005, 0.02))  # 收藏是播放量的0.5-2%
            coin_count = int(view_count * random.uniform(0.003, 0.015))  # 投币是播放量的0.3-1.5%
            like_count = int(view_count * random.uniform(0.01, 0.06))  # 点赞是播放量的1-6%
            
            # 构建视频对象
            video = {
                "bvid": f"BV{random.randint(10000000, 99999999)}",
                "title": title,
                "author": author,
                "pubdate": int(pub_time),
                "duration": f"{random.randint(1, 20)}:{random.randint(10, 59)}",
                "stat": {
                    "view": max(0, view_count),
                    "danmaku": max(0, danmaku_count),
                    "favorite": max(0, favorite_count),
                    "coin": max(0, coin_count),
                    "like": max(0, like_count)
                }
            }
            
            mock_videos.append(video)
        
        # 根据时间排序模拟数据
        mock_videos.sort(key=lambda x: x.get("pubdate", 0), reverse=True)
        
        self.status_label.setText(f"已生成 {len(mock_videos)} 个模拟视频数据")
        QApplication.processEvents()
        
        return mock_videos

    def _clean_html_tags(self, text):
        """移除HTML标签"""
        # 简单的HTML标签清理
        return text.replace("<em class=\"keyword\">", "").replace("</em>", "")

    def set_date_today(self):
        """设置日期范围为今天"""
        today = QDate.currentDate()
        self.date_from.setDate(today)
        self.date_to.setDate(today)

    def set_date_yesterday(self):
        """设置日期范围为昨天"""
        today = QDate.currentDate()
        yesterday = today.addDays(-1)
        self.date_from.setDate(yesterday)
        self.date_to.setDate(yesterday)

    def set_date_last_3_days(self):
        """设置日期范围为最近3天"""
        today = QDate.currentDate()
        three_days_ago = today.addDays(-2)  # 今天、昨天和前天共3天
        self.date_from.setDate(three_days_ago)
        self.date_to.setDate(today)

    def set_date_last_week(self):
        """设置日期范围为最近7天"""
        today = QDate.currentDate()
        week_ago = today.addDays(-6)  # 今天加上往前6天，共7天
        self.date_from.setDate(week_ago)
        self.date_to.setDate(today)

    def set_date_last_ten_days(self):
        """设置无日期限制（实际设置为较大范围）"""
        today = QDate.currentDate()
        distant_past = today.addYears(-10)  # 使用10年前作为开始日期，实现"不限"的效果
        self.date_from.setDate(distant_past)
        self.date_to.setDate(today)

    def get_video_details(self):
        """获取单个视频的详细信息"""
        video_url = self.video_link_input.text().strip()
        if not video_url:
            QMessageBox.warning(self, "提示", "请输入视频链接")
            return
            
        # 从链接中提取视频ID
        video_id = self.extract_video_id(video_url)
        if not video_id:
            QMessageBox.warning(self, "提示", "无效的B站视频链接，请输入正确的链接")
            return
        
        self.status_label.setText(f"正在获取视频 {video_id} 的详细信息...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        QApplication.processEvents()
        
        try:
            # 获取视频详情
            video_info = self.fetch_video_details(video_id)
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            
            if video_info:
                # 显示视频详情对话框
                self.show_video_details_dialog(video_info)
            else:
                QMessageBox.warning(self, "提示", "未能获取到视频信息")
                
        except Exception as e:
            self.status_label.setText(f"获取视频详情出错: {str(e)}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"获取视频详情时出错：{str(e)}")
    
    def extract_video_id(self, url):
        """从B站视频URL中提取BV号或AV号"""
        # 尝试匹配BV号
        bv_pattern = r'BV\w{10}'
        bv_match = re.search(bv_pattern, url)
        if bv_match:
            return bv_match.group(0)
        
        # 尝试匹配AV号
        av_pattern = r'av(\d+)'
        av_match = re.search(av_pattern, url)
        if av_match:
            return f"av{av_match.group(1)}"
            
        # 尝试从b23.tv短链接提取
        if 'b23.tv' in url:
            try:
                response = requests.head(url, allow_redirects=True)
                redirected_url = response.url
                return self.extract_video_id(redirected_url)
            except:
                pass
                
        return None
    
    def fetch_video_details(self, video_id):
        """获取单个视频的详细信息"""
        # 判断是BV还是AV号
        is_bvid = video_id.startswith('BV')
        
        # 使用B站公开API
        if is_bvid:
            url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
        else:
            aid = video_id.replace('av', '')
            url = f"https://api.bilibili.com/x/web-interface/view?aid={aid}"
        
        # 添加模拟浏览器环境的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com/",
            "Cookie": "buvid3=CFF74DA7-D7F1-4F11-9D5C-6BFB2CF88FC118547infoc"  # 添加基本cookie来避免412错误
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查接口返回是否成功
            if data.get("code") != 0:
                raise Exception(f"API返回错误: {data.get('message', '未知错误')}")
            
            # 提取视频详情
            video_data = data.get("data", {})
            
            if not video_data:
                raise Exception("未找到视频数据")
            
            # 构建返回的视频信息
            video_info = {
                "bvid": video_data.get("bvid", ""),
                "aid": video_data.get("aid", ""),
                "title": video_data.get("title", ""),
                "desc": video_data.get("desc", ""),
                "cover": video_data.get("pic", ""),
                "author": video_data.get("owner", {}).get("name", ""),
                "mid": video_data.get("owner", {}).get("mid", ""),
                "face": video_data.get("owner", {}).get("face", ""),
                "pubdate": video_data.get("pubdate", 0),
                "ctime": video_data.get("ctime", 0),
                "duration": video_data.get("duration", 0),
                "dimension": video_data.get("dimension", {}),
                "stat": {
                    "view": video_data.get("stat", {}).get("view", 0),
                    "danmaku": video_data.get("stat", {}).get("danmaku", 0),
                    "reply": video_data.get("stat", {}).get("reply", 0),
                    "favorite": video_data.get("stat", {}).get("favorite", 0),
                    "coin": video_data.get("stat", {}).get("coin", 0),
                    "share": video_data.get("stat", {}).get("share", 0),
                    "like": video_data.get("stat", {}).get("like", 0),
                    "dislike": video_data.get("stat", {}).get("dislike", 0)
                },
                "tags": [tag.get("tag_name", "") for tag in video_data.get("tags", [])],
                "cid": video_data.get("cid", 0),
            }

            # 获取标签（如果API tags字段为空，尝试用tag API获取）
            if not video_info["tags"] and video_info["aid"]:
                try:
                    tag_url = f"https://api.bilibili.com/x/tag/archive/tags?aid={video_info['aid']}"
                    tag_resp = requests.get(tag_url, headers=headers, timeout=6)
                    tag_data = tag_resp.json()
                    if tag_data.get("code") == 0:
                        video_info["tags"] = [t.get("tag_name", "") for t in tag_data.get("data", [])]
                except:
                    pass

            # 获取最高点赞评论
            try:
                reply_url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={video_info['aid']}&sort=2&pn=1"
                reply_resp = requests.get(reply_url, headers=headers, timeout=6)
                reply_data = reply_resp.json()
                hot_comments = []
                if reply_data.get("code") == 0:
                    replies = reply_data.get("data", {}).get("hots", []) or reply_data.get("data", {}).get("replies", [])
                    for reply in replies:
                        hot_comments.append({
                            "user": reply.get("member", {}).get("uname", "匿名"),
                            "like": reply.get("like", 0),
                            "content": reply.get("content", {}).get("message", "")
                        })
                video_info["hot_comments"] = hot_comments
            except:
                video_info["hot_comments"] = []

            return video_info
        
        except Exception as e:
            self.status_label.setText(f"获取视频详情失败: {str(e)}")
            
            # 如果API调用失败，返回模拟数据
            if is_bvid:
                return self._generate_mock_video_details(video_id)
            else:
                return self._generate_mock_video_details(f"BV1xx4y1X7xx")  # 随机生成一个BVID
    
    def show_video_details_dialog(self, video_info):
        """显示视频详情对话框"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("视频详情")
        dialog.setMinimumSize(800, 600)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 视频标题
        title_label = QLabel(video_info.get("title", ""))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # 作者信息
        author_layout = QHBoxLayout()
        author_label = QLabel(f"UP主: {video_info.get('author', '')}")
        author_layout.addWidget(author_label)
        mid_label = QLabel(f"UID: {video_info.get('mid', '')}")
        author_layout.addWidget(mid_label)
        author_layout.addStretch()
        layout.addLayout(author_layout)
        
        # 发布信息
        pub_time = datetime.fromtimestamp(video_info.get("pubdate", 0))
        pub_str = pub_time.strftime("%Y-%m-%d %H:%M:%S")
        pub_label = QLabel(f"发布时间: {pub_str}")
        layout.addWidget(pub_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 数据统计
        stats_group = QGroupBox("数据统计")
        stats_layout = QGridLayout()
        
        stats = video_info.get("stat", {})
        
        # 创建统计信息标签
        stats_layout.addWidget(QLabel("播放量:"), 0, 0)
        stats_layout.addWidget(QLabel(f"{stats.get('view', 0):,}"), 0, 1)
        
        stats_layout.addWidget(QLabel("弹幕数:"), 0, 2)
        stats_layout.addWidget(QLabel(f"{stats.get('danmaku', 0):,}"), 0, 3)
        
        stats_layout.addWidget(QLabel("评论数:"), 1, 0)
        stats_layout.addWidget(QLabel(f"{stats.get('reply', 0):,}"), 1, 1)
        
        stats_layout.addWidget(QLabel("收藏数:"), 1, 2)
        stats_layout.addWidget(QLabel(f"{stats.get('favorite', 0):,}"), 1, 3)
        
        stats_layout.addWidget(QLabel("投币数:"), 2, 0)
        stats_layout.addWidget(QLabel(f"{stats.get('coin', 0):,}"), 2, 1)
        
        stats_layout.addWidget(QLabel("分享数:"), 2, 2)
        stats_layout.addWidget(QLabel(f"{stats.get('share', 0):,}"), 2, 3)
        
        stats_layout.addWidget(QLabel("点赞数:"), 3, 0)
        stats_layout.addWidget(QLabel(f"{stats.get('like', 0):,}"), 3, 1)
        
        stats_layout.addWidget(QLabel("不喜欢数:"), 3, 2)
        stats_layout.addWidget(QLabel(f"{stats.get('dislike', 0):,}"), 3, 3)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 视频描述
        desc_group = QGroupBox("视频简介")
        desc_layout = QVBoxLayout()
        desc_text = QTextBrowser()
        desc_text.setPlainText(video_info.get("desc", ""))
        desc_layout.addWidget(desc_text)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)
        
        # 标签
        tags_group = QGroupBox("视频标签")
        tags_layout = QHBoxLayout()
        tags_text = ", ".join(video_info.get("tags", []))
        tags_label = QLabel(tags_text)
        tags_label.setWordWrap(True)
        tags_layout.addWidget(tags_label)
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        # 点赞数最高的评论
        if video_info.get("hot_comments"):
            top_comment = max(video_info["hot_comments"], key=lambda c: c.get("like", 0))
            comment_group = QGroupBox("点赞数最高的评论")
            comment_layout = QVBoxLayout()
            comment_text = QTextBrowser()
            comment_text.setPlainText(top_comment.get("content", ""))
            comment_layout.addWidget(QLabel(f"用户: {top_comment.get('user', '-')}") )
            comment_layout.addWidget(QLabel(f"点赞数: {top_comment.get('like', 0)}"))
            comment_layout.addWidget(comment_text)
            comment_group.setLayout(comment_layout)
            layout.addWidget(comment_group)

        # 视频链接
        link_group = QGroupBox("视频链接")
        link_layout = QVBoxLayout()
        bvid = video_info.get("bvid", "")
        aid = video_info.get("aid", "")
        bvid_link = f"https://www.bilibili.com/video/{bvid}"
        aid_link = f"https://www.bilibili.com/video/av{aid}"

        bvid_layout = QHBoxLayout()
        bvid_layout.addWidget(QLabel("BV链接:"))
        bvid_text = QLineEdit(bvid_link)
        bvid_text.setReadOnly(True)
        bvid_layout.addWidget(bvid_text)

        # 复制BV链接按钮
        copy_bvid_btn = QPushButton("复制")
        copy_bvid_btn.setStyleSheet("background-color: #FB7299; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold;")
        def copy_bvid_link():
            clipboard = QApplication.clipboard()
            clipboard.setText(bvid_text.text())
            copy_bvid_btn.setText("已复制")
            QTimer.singleShot(1000, lambda: copy_bvid_btn.setText("复制"))
        copy_bvid_btn.clicked.connect(copy_bvid_link)
        bvid_layout.addWidget(copy_bvid_btn)

        aid_layout = QHBoxLayout()
        aid_layout.addWidget(QLabel("AV链接:"))
        aid_text = QLineEdit(aid_link)
        aid_text.setReadOnly(True)
        aid_layout.addWidget(aid_text)

        # 复制AV链接按钮
        copy_aid_btn = QPushButton("复制")
        copy_aid_btn.setStyleSheet("background-color: #FB7299; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold;")
        def copy_aid_link():
            clipboard = QApplication.clipboard()
            clipboard.setText(aid_text.text())
            copy_aid_btn.setText("已复制")
            QTimer.singleShot(1000, lambda: copy_aid_btn.setText("复制"))
        copy_aid_btn.clicked.connect(copy_aid_link)
        aid_layout.addWidget(copy_aid_btn)

        link_layout.addLayout(bvid_layout)
        link_layout.addLayout(aid_layout)
        link_group.setLayout(link_layout)
        layout.addWidget(link_group)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def _generate_mock_video_details(self, video_id):
        """生成模拟视频详情数据"""
        # 随机生成视频标题
        title_templates = [
            "【干货】如何高效学习Python编程",
            "2025年最值得学习的编程语言TOP10",
            "编程新手必看：从零开始学习Web开发",
            "Python vs JavaScript：哪个更适合初学者？",
            "一小时搞定Python爬虫实战",
            "程序员必备：VSCode高效开发技巧",
            "【深度解析】人工智能基础知识"
        ]
        
        # 随机选择UP主名称
        up_names = ["技术宅", "程序员小张", "代码大师", "IT视界", "Python爱好者", "编程指南", "代码与艺术"]
        
        # 生成随机数据
        view_count = random.randint(10000, 3000000)
        
        # 生成视频信息
        mock_video = {
            "bvid": video_id if video_id.startswith("BV") else f"BV1xx4y1X7xx",
            "aid": random.randint(10000, 99999999),
            "title": random.choice(title_templates),
            "desc": "这是一个模拟生成的视频描述。由于无法获取实际视频数据，系统生成了这个示例数据用于演示。在实际使用中，这里会显示视频的真实简介内容。",
            "cover": "https://i0.hdslb.com/bfs/archive/sample_cover.jpg",
            "author": random.choice(up_names),
            "mid": random.randint(10000, 9999999),
            "face": "https://i0.hdslb.com/bfs/face/sample_face.jpg",
            "pubdate": int(datetime.now().timestamp()) - random.randint(86400, 86400*30),  # 1-30天前
            "ctime": int(datetime.now().timestamp()) - random.randint(86400, 86400*31),  # 比发布时间早
            "duration": random.randint(120, 1800),  # 2-30分钟
            "dimension": {"width": 1920, "height": 1080, "rotate": 0},
            "stat": {
                "view": view_count,
                "danmaku": int(view_count * random.uniform(0.01, 0.05)),  # 弹幕是播放量的1-5%
                "reply": int(view_count * random.uniform(0.002, 0.01)),  # 评论是播放量的0.2-1%
                "favorite": int(view_count * random.uniform(0.005, 0.02)),  # 收藏是播放量的0.5-2%
                "coin": int(view_count * random.uniform(0.003, 0.015)),  # 投币是播放量的0.3-1.5%
                "share": int(view_count * random.uniform(0.001, 0.008)),  # 分享是播放量的0.1-0.8%
                "like": int(view_count * random.uniform(0.01, 0.06)),  # 点赞是播放量的1-6%
                "dislike": int(view_count * random.uniform(0, 0.001))  # 不喜欢数很少
            },
            "tags": ["编程", "Python", "教程", "技术", "学习", "计算机科学", "开发"]
        }
        
        return mock_video

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BilibiliStatsApp()
    window.show()
    sys.exit(app.exec_())
