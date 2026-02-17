"""
Main window for RPA Lab GUI.
Contains the main layout with sidebar and content panels.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Callable, Dict, List, Optional
from datetime import datetime
from loguru import logger

from src.utils.config import config
from src.database.db_manager import db
from src.models.task import Task, TaskStatus
from src.models.action import Action, ActionType
from src.models.variable import Variable
from src.models.schedule import Schedule, ScheduleType
from src.models.execution_log import ExecutionLog
from src.core.recorder import Recorder
from src.core.player import Player
from src.core.scheduler import task_scheduler
from src.core.speed_controller import SpeedMode


class MainWindow(ctk.CTkFrame):
    """
    Main application window with sidebar navigation and content panels.
    """
    
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        
        # Configure background and grid
        self.configure(fg_color=("gray92", "gray14"))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Initialize components
        self.recorder = Recorder()
        self.player = Player()
        
        # Current state
        self.current_task: Optional[Task] = None
        self.current_actions: List[Action] = []
        self.is_recording = False
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Initialize content_frames dictionary first
        self.content_frames = {}
        
        # Create UI components
        self._create_sidebar()
        self._create_content_area()
        
        # Start scheduler
        task_scheduler.start()
        
        # Set initial selection (update buttons only, panel already shown)
        for k, btn in self.nav_buttons.items():
            if k == "tasks":
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        
        # Load initial data
        self._load_tasks()
    
    def _setup_callbacks(self):
        """Setup callbacks for recorder and player."""
        self.recorder.action_callback = self._on_action_recorded
        self.recorder.stop_callback = self._on_recording_stopped
        
        self.player.on_progress = self._on_execution_progress
        self.player.on_task_complete = self._on_task_complete
    
    def _create_sidebar(self):
        """Create the left sidebar with navigation."""
        self.sidebar = ctk.CTkFrame(self, width=250)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        self.sidebar.grid_propagate(False)
        
        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=f"🤖 {config.app_name}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.pack(pady=20, padx=10)
        
        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=10, pady=10)
        
        self.nav_buttons = {}
        nav_items = [
            ("tasks", "📋 Tarefas", self._show_tasks_panel),
            ("record", "⏺️ Gravar", self._show_record_panel),
            ("schedule", "📅 Agendamentos", self._show_schedule_panel),
            ("history", "📊 Histórico", self._show_history_panel),
            ("settings", "⚙️ Configurações", self._show_settings_panel),
        ]
        
        for key, text, command in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                command=lambda c=command, k=key: self._on_nav_click(k, c),
                height=40,
                anchor="w",
                fg_color="transparent",
                hover_color=("gray75", "gray25")
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn
        
        # Quick actions
        self.quick_frame = ctk.CTkFrame(self.sidebar)
        self.quick_frame.pack(fill="x", padx=10, pady=20)
        
        self.quick_label = ctk.CTkLabel(
            self.quick_frame,
            text="Ações Rápidas",
            font=ctk.CTkFont(weight="bold")
        )
        self.quick_label.pack(pady=5)
        
        self.record_btn = ctk.CTkButton(
            self.quick_frame,
            text="⏺️ Nova Gravação",
            command=self._start_quick_recording,
            fg_color="red",
            hover_color="darkred"
        )
        self.record_btn.pack(fill="x", padx=5, pady=2)
        
        # Status
        self.status_frame = ctk.CTkFrame(self.sidebar)
        self.status_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Pronto",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Note: Don't set initial selection here - wait for content to be created
    
    def _create_content_area(self):
        """Create the main content area."""
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, sticky="nswe", padx=5, pady=5)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        
        # Create all panels (they will be shown/hidden via grid)
        self._create_tasks_panel()
        self._create_record_panel()
        self._create_schedule_panel()
        self._create_history_panel()
        self._create_settings_panel()
        
        # Show tasks panel by default
        self._show_panel("tasks")
    
    def _on_nav_click(self, key: str, command: Callable):
        """Handle navigation button click."""
        # Update button styles
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        
        # Execute command
        command()
    
    def _show_panel(self, panel_name: str):
        """Show a specific panel and hide others."""
        for name, frame in self.content_frames.items():
            if name == panel_name:
                frame.grid(row=0, column=0, sticky="nswe")
            else:
                frame.grid_forget()
    
    # ==================== TASKS PANEL ====================
    
    def _create_tasks_panel(self):
        """Create the tasks management panel."""
        self.tasks_frame = ctk.CTkFrame(self.content)
        self.content_frames["tasks"] = self.tasks_frame
        
        # Header
        header = ctk.CTkFrame(self.tasks_frame)
        header.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Gerenciador de Tarefas",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        new_btn = ctk.CTkButton(
            header,
            text="+ Nova Tarefa",
            command=self._new_task
        )
        new_btn.pack(side="right", padx=10)
        
        # Tasks list
        self.tasks_list_frame = ctk.CTkScrollableFrame(self.tasks_frame)
        self.tasks_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Task details frame (initially hidden)
        self.task_detail_frame = ctk.CTkFrame(self.tasks_frame)
    
    def _show_tasks_panel(self):
        """Show tasks panel and refresh data."""
        self._show_panel("tasks")
        self._load_tasks()
    
    def _load_tasks(self):
        """Load and display all tasks."""
        # Clear existing widgets
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
        
        # Get tasks from database
        tasks = db.get_all_tasks()
        
        if not tasks:
            empty_label = ctk.CTkLabel(
                self.tasks_list_frame,
                text="Nenhuma tarefa encontrada.\nClique em '+ Nova Tarefa' para começar.",
                font=ctk.CTkFont(size=14)
            )
            empty_label.pack(pady=50)
            return
        
        for task in tasks:
            self._create_task_card(task)
    
    def _create_task_card(self, task: Task):
        """Create a task card widget."""
        card = ctk.CTkFrame(self.tasks_list_frame)
        card.pack(fill="x", pady=5)
        
        # Task info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=task.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x")
        
        desc_label = ctk.CTkLabel(
            info_frame,
            text=task.description or "Sem descrição",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        desc_label.pack(fill="x")
        
        # Stats
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=5)
        
        stats_text = f"Execuções: {task.total_runs} | Sucesso: {task.successful_runs} | Taxa: {task.success_rate:.0f}%"
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        stats_label.pack(side="left")
        
        # Actions
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        run_btn = ctk.CTkButton(
            actions_frame,
            text="▶️ Executar",
            width=80,
            command=lambda t=task: self._run_task(t)
        )
        run_btn.pack(side="left", padx=2)
        
        edit_btn = ctk.CTkButton(
            actions_frame,
            text="✏️ Editar",
            width=80,
            fg_color="gray",
            command=lambda t=task: self._edit_task(t)
        )
        edit_btn.pack(side="left", padx=2)
        
        schedule_btn = ctk.CTkButton(
            actions_frame,
            text="📅 Agendar",
            width=80,
            fg_color="purple",
            command=lambda t=task: self._schedule_task(t)
        )
        schedule_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️",
            width=40,
            fg_color="red",
            hover_color="darkred",
            command=lambda t=task: self._delete_task(t)
        )
        delete_btn.pack(side="right", padx=2)
    
    def _new_task(self):
        """Create a new task."""
        dialog = TaskDialog(self, "Nova Tarefa")
        if dialog.result:
            task = Task(name=dialog.result["name"], description=dialog.result["description"])
            task = db.create_task(task)
            self._edit_task(task)
            self._load_tasks()
    
    def _edit_task(self, task: Task):
        """Open task editor."""
        self.current_task = task
        self.current_actions = db.get_task_actions(task.id)
        self._show_record_panel()
        self._load_task_in_editor(task)
    
    def _delete_task(self, task: Task):
        """Delete a task after confirmation."""
        if messagebox.askyesno("Confirmar", f"Deseja excluir a tarefa '{task.name}'?"):
            db.delete_task(task.id)
            self._load_tasks()
    
    def _run_task(self, task: Task):
        """Execute a task."""
        actions = db.get_task_actions(task.id)
        variables = db.get_task_variables(task.id)
        
        var_dict = {v.name: v.get_single_value() for v in variables}
        
        # Run in background
        self.player.play_task_async(
            task=task,
            actions=actions,
            variables=var_dict,
            speed_mode=task.speed_mode
        )
        
        self.status_label.configure(text=f"Status: Executando {task.name}...")
    
    def _schedule_task(self, task: Task):
        """Open schedule dialog for task."""
        dialog = ScheduleDialog(self, task)
        if dialog.result:
            schedule = dialog.result
            schedule.task_id = task.id
            db.create_schedule(schedule)
            task_scheduler.add_schedule(schedule)
            self.status_label.configure(text=f"Agendamento criado para {task.name}")
    
    # ==================== RECORD PANEL ====================
    
    def _create_record_panel(self):
        """Create the recording panel."""
        self.record_frame = ctk.CTkFrame(self.content)
        self.content_frames["record"] = self.record_frame
        
        # Header with controls
        header = ctk.CTkFrame(self.record_frame)
        header.pack(fill="x", padx=10, pady=10)
        
        # Task name entry
        self.task_name_entry = ctk.CTkEntry(
            header,
            placeholder_text="Nome da tarefa",
            width=200
        )
        self.task_name_entry.pack(side="left", padx=10)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            header,
            text="💾 Salvar",
            command=self._save_task,
            fg_color="green"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Recording controls
        controls_frame = ctk.CTkFrame(header)
        controls_frame.pack(side="right", padx=10)
        
        self.rec_btn = ctk.CTkButton(
            controls_frame,
            text="⏺️ Gravar",
            command=self._toggle_recording,
            fg_color="red",
            width=100
        )
        self.rec_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            controls_frame,
            text="🗑️ Limpar",
            command=self._clear_actions,
            fg_color="gray"
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Actions list
        list_frame = ctk.CTkFrame(self.record_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Action list header
        list_header = ctk.CTkFrame(list_frame)
        list_header.pack(fill="x")
        
        ctk.CTkLabel(list_header, text="Ações", width=50).pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="Tipo", width=150).pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="Detalhes", width=300).pack(side="left", padx=5)
        ctk.CTkLabel(list_header, text="Delay (s)", width=80).pack(side="left", padx=5)
        
        # Scrollable action list
        self.actions_list = ctk.CTkScrollableFrame(list_frame)
        self.actions_list.pack(fill="both", expand=True)
        
        # Manual action buttons
        manual_frame = ctk.CTkFrame(self.record_frame)
        manual_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(manual_frame, text="Adicionar ação:").pack(side="left", padx=5)
        
        actions = [
            ("Click", lambda: self._add_manual_action(ActionType.CLICK)),
            ("Digitar", lambda: self._add_manual_action(ActionType.TYPE_TEXT)),
            ("Hotkey", lambda: self._add_manual_action(ActionType.HOTKEY)),
            ("Wait", lambda: self._add_manual_action(ActionType.WAIT)),
            ("Imagem", lambda: self._add_manual_action(ActionType.IMAGE_CLICK)),
        ]
        
        for text, command in actions:
            btn = ctk.CTkButton(
                manual_frame,
                text=text,
                command=command,
                width=80,
                fg_color="gray"
            )
            btn.pack(side="left", padx=2)
        
        # Speed control
        speed_frame = ctk.CTkFrame(self.record_frame)
        speed_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(speed_frame, text="Velocidade:").pack(side="left", padx=5)
        
        self.speed_var = ctk.StringVar(value="normal")
        speed_menu = ctk.CTkOptionMenu(
            speed_frame,
            variable=self.speed_var,
            values=["normal", "fast", "turbo", "instant"],
            width=100
        )
        speed_menu.pack(side="left", padx=5)
    
    def _show_record_panel(self):
        """Show record panel."""
        self._show_panel("record")
    
    def _load_task_in_editor(self, task: Task):
        """Load a task into the editor."""
        self.task_name_entry.delete(0, "end")
        self.task_name_entry.insert(0, task.name)
        self.speed_var.set(task.speed_mode)
        self._refresh_actions_list()
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if self.is_recording:
            self.recorder.stop_recording()
            self.rec_btn.configure(text="⏺️ Gravar", fg_color="red")
            self.record_btn.configure(text="⏺️ Nova Gravação", fg_color="red")
            self.is_recording = False
            self.status_label.configure(text=f"Status: Gravação parada - {len(self.current_actions)} ações")
        else:
            # Clear previous actions for new recording
            if not self.current_task:
                self.current_actions = []
            self.recorder.start_recording()
            self.rec_btn.configure(text="⏹️ Parar", fg_color="orange")
            self.record_btn.configure(text="⏹️ Parar Gravação", fg_color="orange")
            self.is_recording = True
            self.status_label.configure(text="Status: GRAVANDO... Execute ações e pressione ESC para parar")
            self._refresh_actions_list()
    
    def _start_quick_recording(self):
        """Start quick recording (creates new task)."""
        if not self.is_recording:
            self._show_record_panel()
            self.task_name_entry.delete(0, "end")
            self.task_name_entry.insert(0, f"Nova Tarefa {datetime.now().strftime('%Y%m%d_%H%M')}")
            self.current_task = None
            self.current_actions = []
            self._toggle_recording()
    
    def _on_action_recorded(self, action: Action):
        """Callback when an action is recorded."""
        self.current_actions.append(action)
        self._refresh_actions_list()
    
    def _on_recording_stopped(self):
        """Callback when recording stops."""
        self.is_recording = False
        self.rec_btn.configure(text="⏺️ Gravar", fg_color="red")
        self.record_btn.configure(text="⏺️ Nova Gravação", fg_color="red")
    
    def _refresh_actions_list(self):
        """Refresh the actions list display."""
        # Clear existing
        for widget in self.actions_list.winfo_children():
            widget.destroy()
        
        for i, action in enumerate(self.current_actions):
            self._create_action_row(i, action)
    
    def _create_action_row(self, index: int, action: Action):
        """Create a row for an action."""
        row = ctk.CTkFrame(self.actions_list)
        row.pack(fill="x", pady=2)
        
        # Index
        ctk.CTkLabel(row, text=str(index + 1), width=50).pack(side="left", padx=5)
        
        # Type - handle both string and enum
        action_type_value = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
        type_text = action_type_value.replace("_", " ").title()
        ctk.CTkLabel(row, text=type_text, width=150).pack(side="left", padx=5)
        
        # Details
        details = self._get_action_details(action)
        ctk.CTkLabel(row, text=details, width=300, anchor="w").pack(side="left", padx=5)
        
        # Delay
        ctk.CTkLabel(row, text=f"{action.delay_after:.2f}", width=80).pack(side="left", padx=5)
        
        # Delete button
        del_btn = ctk.CTkButton(
            row,
            text="✕",
            width=30,
            fg_color="transparent",
            hover_color="red",
            command=lambda: self._delete_action(index)
        )
        del_btn.pack(side="right", padx=5)
    
    def _get_action_details(self, action: Action) -> str:
        """Get details string for an action."""
        # Handle both string and enum action_type
        action_type_str = action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type)
        
        if action_type_str in ["click", "double_click", "right_click"]:
            return f"({action.x}, {action.y})"
        elif action_type_str == "type_text":
            text = action.text or ""
            return f'"{text[:30]}{"..." if len(text) > 30 else ""}"'
        elif action_type_str == "hotkey":
            return "+".join(action.keys)
        elif action_type_str == "wait":
            return f"{action.duration}s"
        elif action_type_str == "image_click":
            return action.image_path or "Imagem"
        elif action_type_str == "scroll":
            return f"Scroll: {action.scroll_amount}"
        return ""
    
    def _delete_action(self, index: int):
        """Delete an action."""
        if 0 <= index < len(self.current_actions):
            del self.current_actions[index]
            self._refresh_actions_list()
    
    def _clear_actions(self):
        """Clear all actions."""
        self.current_actions = []
        self._refresh_actions_list()
    
    def _add_manual_action(self, action_type: ActionType):
        """Add a manual action."""
        dialog = ActionDialog(self, action_type)
        if dialog.result:
            self.current_actions.append(dialog.result)
            self._refresh_actions_list()
    
    def _save_task(self):
        """Save the current task."""
        name = self.task_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Digite um nome para a tarefa")
            return
        
        if not self.current_actions:
            messagebox.showwarning("Aviso", "Adicione pelo menos uma ação")
            return
        
        if self.current_task:
            # Update existing task
            self.current_task.name = name
            self.current_task.speed_mode = self.speed_var.get()
            self.current_task.status = TaskStatus.READY
            db.update_task(self.current_task)
            
            # Delete old actions
            for action in db.get_task_actions(self.current_task.id):
                db.delete_action(action.id)
            
            task_id = self.current_task.id
        else:
            # Create new task
            task = Task(name=name, status=TaskStatus.READY, speed_mode=self.speed_var.get())
            task = db.create_task(task)
            task_id = task.id
        
        # Save actions
        for i, action in enumerate(self.current_actions):
            action.task_id = task_id
            action.order_index = i
            db.create_action(action)
        
        self.status_label.configure(text=f"Tarefa '{name}' salva com sucesso!")
        messagebox.showinfo("Sucesso", "Tarefa salva com sucesso!")
    
    # ==================== SCHEDULE PANEL ====================
    
    def _create_schedule_panel(self):
        """Create the schedule management panel."""
        self.schedule_frame = ctk.CTkFrame(self.content)
        self.content_frames["schedule"] = self.schedule_frame
        
        # Header
        header = ctk.CTkFrame(self.schedule_frame)
        header.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Agendamentos",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # Schedule list
        self.schedule_list = ctk.CTkScrollableFrame(self.schedule_frame)
        self.schedule_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _show_schedule_panel(self):
        """Show schedule panel."""
        self._show_panel("schedule")
        self._load_schedules()
    
    def _load_schedules(self):
        """Load all schedules."""
        for widget in self.schedule_list.winfo_children():
            widget.destroy()
        
        jobs = task_scheduler.get_all_jobs()
        
        if not jobs:
            empty_label = ctk.CTkLabel(
                self.schedule_list,
                text="Nenhum agendamento ativo.",
                font=ctk.CTkFont(size=14)
            )
            empty_label.pack(pady=50)
            return
        
        for job in jobs:
            self._create_schedule_card(job)
    
    def _create_schedule_card(self, job: Dict):
        """Create a schedule card."""
        card = ctk.CTkFrame(self.schedule_list)
        card.pack(fill="x", pady=5)
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=job["name"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(anchor="w")
        
        next_run = job.get("next_run")
        if next_run:
            next_text = f"Próxima execução: {next_run.strftime('%d/%m/%Y %H:%M')}"
        else:
            next_text = "Sem próxima execução"
        
        next_label = ctk.CTkLabel(
            info_frame,
            text=next_text,
            font=ctk.CTkFont(size=12)
        )
        next_label.pack(anchor="w")
        
        trigger_label = ctk.CTkLabel(
            info_frame,
            text=f"Trigger: {job['trigger']}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        trigger_label.pack(anchor="w")
    
    # ==================== HISTORY PANEL ====================
    
    def _create_history_panel(self):
        """Create the execution history panel."""
        self.history_frame = ctk.CTkFrame(self.content)
        self.content_frames["history"] = self.history_frame
        
        # Header
        header = ctk.CTkFrame(self.history_frame)
        header.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Histórico de Execuções",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(
            header,
            text="🔄 Atualizar",
            command=self._load_history
        )
        refresh_btn.pack(side="right", padx=10)
        
        # History list
        self.history_list = ctk.CTkScrollableFrame(self.history_frame)
        self.history_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _show_history_panel(self):
        """Show history panel."""
        self._show_panel("history")
        self._load_history()
    
    def _load_history(self):
        """Load execution history."""
        for widget in self.history_list.winfo_children():
            widget.destroy()
        
        logs = db.get_recent_execution_logs(50)
        
        if not logs:
            empty_label = ctk.CTkLabel(
                self.history_list,
                text="Nenhuma execução registrada.",
                font=ctk.CTkFont(size=14)
            )
            empty_label.pack(pady=50)
            return
        
        for log in logs:
            self._create_history_card(log)
    
    def _create_history_card(self, log: ExecutionLog):
        """Create a history card."""
        card = ctk.CTkFrame(self.history_list)
        card.pack(fill="x", pady=5)
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Task name and status
        status_color = "green" if log.is_success else "red"
        status_text = "✓ Sucesso" if log.is_success else "✗ Falhou"
        
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill="x")
        
        name_label = ctk.CTkLabel(
            name_frame,
            text=log.task_name or f"Tarefa {log.task_id}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.pack(side="left")
        
        status_label = ctk.CTkLabel(
            name_frame,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        )
        status_label.pack(side="right")
        
        # Details
        if log.started_at:
            time_text = log.started_at.strftime('%d/%m/%Y %H:%M:%S')
            if log.duration_seconds:
                time_text += f" ({log.duration_seconds:.1f}s)"
            
            time_label = ctk.CTkLabel(
                info_frame,
                text=time_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            time_label.pack(anchor="w")
        
        # Error message
        if log.error_message:
            error_label = ctk.CTkLabel(
                info_frame,
                text=f"Erro: {log.error_message[:50]}...",
                font=ctk.CTkFont(size=11),
                text_color="red"
            )
            error_label.pack(anchor="w")
    
    # ==================== SETTINGS PANEL ====================
    
    def _create_settings_panel(self):
        """Create the settings panel."""
        self.settings_frame = ctk.CTkFrame(self.content)
        self.content_frames["settings"] = self.settings_frame
        
        # Header
        header = ctk.CTkFrame(self.settings_frame)
        header.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            header,
            text="Configurações",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # Settings content
        content = ctk.CTkFrame(self.settings_frame)
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Theme
        theme_frame = ctk.CTkFrame(content)
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(theme_frame, text="Tema:").pack(side="left", padx=10)
        
        self.theme_var = ctk.StringVar(value=config.theme)
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["dark", "light"],
            command=lambda v: self.app.set_theme(v)
        )
        theme_menu.pack(side="left", padx=10)
        
        # About
        about_frame = ctk.CTkFrame(content)
        about_frame.pack(fill="x", pady=20)
        
        about_text = f"""
        {config.app_name} v{config.app_version}
        
        Sistema de Automação de Processos Robóticos
        
        Recursos:
        • Gravação e reprodução de ações
        • Reconhecimento de imagem
        • Variáveis reutilizáveis
        • Agendamento de tarefas
        • Controle de velocidade
        """
        
        about_label = ctk.CTkLabel(
            about_frame,
            text=about_text,
            justify="left"
        )
        about_label.pack(padx=10, pady=10)
    
    def _show_settings_panel(self):
        """Show settings panel."""
        self._show_panel("settings")
    
    # ==================== CALLBACKS ====================
    
    def _on_execution_progress(self, current: int, total: int):
        """Callback for execution progress."""
        self.status_label.configure(text=f"Status: Executando {current}/{total}")
    
    def _on_task_complete(self, task: Task, success: bool):
        """Callback when task execution completes."""
        status = "concluída" if success else "falhou"
        self.status_label.configure(text=f"Status: Tarefa {task.name} {status}")
        self._load_history()


class TaskDialog(ctk.CTkToplevel):
    """Dialog for creating/editing a task."""
    
    def __init__(self, parent, title: str, task: Optional[Task] = None):
        super().__init__(parent)
        
        self.result = None
        self.task = task
        
        self.title(title)
        self.geometry("400x200")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Content
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Name
        ctk.CTkLabel(self.content, text="Nome:").pack(anchor="w")
        self.name_entry = ctk.CTkEntry(self.content, width=300)
        self.name_entry.pack(fill="x", pady=5)
        
        if task:
            self.name_entry.insert(0, task.name)
        
        # Description
        ctk.CTkLabel(self.content, text="Descrição:").pack(anchor="w")
        self.desc_entry = ctk.CTkEntry(self.content, width=300)
        self.desc_entry.pack(fill="x", pady=5)
        
        if task and task.description:
            self.desc_entry.insert(0, task.description)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save).pack(side="right", padx=5)
        
        self.wait_window()
    
    def _save(self):
        """Save the dialog."""
        name = self.name_entry.get().strip()
        if not name:
            return
        
        self.result = {
            "name": name,
            "description": self.desc_entry.get().strip()
        }
        self.destroy()
    
    def _cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()


class ScheduleDialog(ctk.CTkToplevel):
    """Dialog for creating a schedule."""
    
    def __init__(self, parent, task: Task):
        super().__init__(parent)
        
        self.result = None
        self.task = task
        
        self.title(f"Agendar: {task.name}")
        self.geometry("400x350")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Content
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Schedule type
        ctk.CTkLabel(self.content, text="Tipo:").pack(anchor="w")
        self.type_var = ctk.StringVar(value="daily")
        type_menu = ctk.CTkOptionMenu(
            self.content,
            variable=self.type_var,
            values=["daily", "weekly", "monthly", "interval"]
        )
        type_menu.pack(fill="x", pady=5)
        
        # Time
        ctk.CTkLabel(self.content, text="Horário (HH:MM):").pack(anchor="w")
        self.time_entry = ctk.CTkEntry(self.content)
        self.time_entry.insert(0, "09:00")
        self.time_entry.pack(fill="x", pady=5)
        
        # Day of week (for weekly)
        ctk.CTkLabel(self.content, text="Dias da semana (0-6, Seg-Dom):").pack(anchor="w")
        self.days_entry = ctk.CTkEntry(self.content)
        self.days_entry.insert(0, "0,1,2,3,4")
        self.days_entry.pack(fill="x", pady=5)
        
        # Day of month (for monthly)
        ctk.CTkLabel(self.content, text="Dia do mês (1-31):").pack(anchor="w")
        self.day_entry = ctk.CTkEntry(self.content)
        self.day_entry.insert(0, "1")
        self.day_entry.pack(fill="x", pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Salvar", command=self._save).pack(side="right", padx=5)
        
        self.wait_window()
    
    def _save(self):
        """Save the schedule."""
        schedule_type = ScheduleType(self.type_var.get())
        time_str = self.time_entry.get().strip()
        
        schedule = Schedule(
            task_id=self.task.id,
            schedule_type=schedule_type,
            is_active=True
        )
        schedule.time = time_str
        
        if schedule_type == ScheduleType.WEEKLY:
            days = [int(d.strip()) for d in self.days_entry.get().split(",")]
            schedule.days_of_week = days
        elif schedule_type == ScheduleType.MONTHLY:
            schedule.day_of_month = int(self.day_entry.get())
        elif schedule_type == ScheduleType.INTERVAL:
            schedule.interval_minutes = int(self.day_entry.get())  # Reuse field
        
        self.result = schedule
        self.destroy()
    
    def _cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()


class ActionDialog(ctk.CTkToplevel):
    """Dialog for adding a manual action."""
    
    def __init__(self, parent, action_type: ActionType):
        super().__init__(parent)
        
        self.result = None
        self.action_type = action_type
        
        self.title(f"Adicionar: {action_type.value}")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        # Content
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Type-specific fields
        self._create_fields()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, side="bottom")
        
        ctk.CTkButton(btn_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Adicionar", command=self._save).pack(side="right", padx=5)
        
        self.wait_window()
    
    def _create_fields(self):
        """Create fields based on action type."""
        if self.action_type == ActionType.CLICK:
            ctk.CTkLabel(self.content, text="Posição X:").pack(anchor="w")
            self.x_entry = ctk.CTkEntry(self.content)
            self.x_entry.pack(fill="x", pady=5)
            
            ctk.CTkLabel(self.content, text="Posição Y:").pack(anchor="w")
            self.y_entry = ctk.CTkEntry(self.content)
            self.y_entry.pack(fill="x", pady=5)
        
        elif self.action_type == ActionType.TYPE_TEXT:
            ctk.CTkLabel(self.content, text="Texto:").pack(anchor="w")
            self.text_entry = ctk.CTkEntry(self.content)
            self.text_entry.pack(fill="x", pady=5)
        
        elif self.action_type == ActionType.HOTKEY:
            ctk.CTkLabel(self.content, text="Teclas (separadas por vírgula):").pack(anchor="w")
            self.keys_entry = ctk.CTkEntry(self.content)
            self.keys_entry.insert(0, "ctrl,c")
            self.keys_entry.pack(fill="x", pady=5)
        
        elif self.action_type == ActionType.WAIT:
            ctk.CTkLabel(self.content, text="Duração (segundos):").pack(anchor="w")
            self.duration_entry = ctk.CTkEntry(self.content)
            self.duration_entry.insert(0, "1.0")
            self.duration_entry.pack(fill="x", pady=5)
        
        elif self.action_type == ActionType.IMAGE_CLICK:
            ctk.CTkLabel(self.content, text="Caminho da imagem:").pack(anchor="w")
            
            # Frame for image path and browse button
            image_frame = ctk.CTkFrame(self.content, fg_color="transparent")
            image_frame.pack(fill="x", pady=5)
            
            self.image_entry = ctk.CTkEntry(image_frame)
            self.image_entry.pack(side="left", fill="x", expand=True)
            
            browse_btn = ctk.CTkButton(
                image_frame,
                text="📁 Localizar",
                width=80,
                command=self._browse_image
            )
            browse_btn.pack(side="right", padx=(5, 0))
            
            ctk.CTkLabel(self.content, text="Confiança (0.0-1.0):").pack(anchor="w")
            self.confidence_entry = ctk.CTkEntry(self.content)
            self.confidence_entry.insert(0, "0.9")
            self.confidence_entry.pack(fill="x", pady=5)
    
    def _browse_image(self):
        """Open file browser to select an image."""
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Arquivos de Imagem", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Todos os Arquivos", "*.*")
            ]
        )
        if file_path:
            self.image_entry.delete(0, "end")
            self.image_entry.insert(0, file_path)
    
    def _save(self):
        """Save the action."""
        action = None
        
        if self.action_type == ActionType.CLICK:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            action = Action.create_click(x, y)
        
        elif self.action_type == ActionType.TYPE_TEXT:
            text = self.text_entry.get()
            action = Action.create_type_text(text)
        
        elif self.action_type == ActionType.HOTKEY:
            keys = [k.strip() for k in self.keys_entry.get().split(",")]
            action = Action.create_hotkey(keys)
        
        elif self.action_type == ActionType.WAIT:
            duration = float(self.duration_entry.get())
            action = Action.create_wait(duration)
        
        elif self.action_type == ActionType.IMAGE_CLICK:
            image_path = self.image_entry.get()
            confidence = float(self.confidence_entry.get())
            action = Action.create_image_click(image_path, confidence)
        
        self.result = action
        self.destroy()
    
    def _cancel(self):
        """Cancel the dialog."""
        self.result = None
        self.destroy()