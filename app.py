import pandas as pd
import streamlit as st
import os
import tempfile
from datetime import datetime
import base64
from io import BytesIO

class ProblemAnalyzer:
    def __init__(self):
        self.results = []
        self.subjects = {}  # 教科ごとのデータフレームを管理
        self.current_subject = "未設定"  # 現在の教科
        self.groups = {
          1: "得意な問題のグループ\n発展問題に挑戦する\n解法を他人に説明する\n別視点の解法で解いてみる",
          2: "確認が必要なグループ\n解答を読み直して再度解く\n類似問題を解いて定着を図る",
          3: "計算ミスの傾向を修正\nミスのパターンを分析し、注意点をまとめる\n丁寧に計算する練習を行う",
          4: "一時的なミス\n同じ問題を解いて再確認する\n次の問題に挑む",
          5: "基礎知識の再暗記\\n暗記カードやノートを使用して基本事項を再暗記する\n毎日繰り返し復習する",
          6: "応用知識の補強\n教科書や参考書の該当範囲を復習する\n応用問題に取り組み理解を深める",
          7: "応用力の強化\n類似問題を複数解いて応用力を養う\n解法のパターンを整理し、ほかの問題に応用する",
          8: "基礎からのやり直し\n基礎的な問題からやり直し、理解を固める\n解説を読み基本を確認する",
          9: "用語知識の補強\n用語集や辞書を使って用語の意味を確認する\nまとめノートを作成し,定期的に見直す",
          10: "読解力の向上\n国語の読解問題や、要約の練習を行う\n読書の時間を確保し、読解力を高める。",
          11: "根本的な理解の深化\n教科書や参考書を読み直す\n先生や友人に質問をして理解を深める"
        }

    def set_subject(self, subject_name):
        if subject_name and subject_name != "":
            self.current_subject = subject_name
            if subject_name not in self.subjects:
                self.subjects[subject_name] = []
            self.results = self.subjects[subject_name]
            return f"教科「{subject_name}」の分析を開始します。"
        else:
            return "教科名を入力してください。"

    def analyze_problem(self, subject_input, problem_number, correct, hesitation=None, cause=None, mistake=None, knowledge=None, experience=None, issue=None, comment=""):
        if not all([problem_number, correct]):
            return "問題番号と正解状況を選択してください。"
        if not subject_input:
            return "教科名を入力してください。"
        try:
            if correct == "正解":
                group = 1 if hesitation == "スムーズに解けた" else 2
            else:
                if cause == "計算ミスやケアレスミス":
                    group = 3 if mistake == "同じミスを繰り返している" else 4
                elif cause == "知識不足":
                    group = 5 if knowledge == "基本事項の暗記ミス" else 6
                elif cause == "解法が思いつかない":
                    group = 7 if experience == "類似問題の経験あり" else 8
                elif cause == "問題文の理解不足":
                    group = {"用語の意味が分からない": 9, "問題文の日本語が難しい": 10, "解答を読んでも理解できない": 11}[issue]
                else:
                    return "原因を選択してください。"

            # 重複問題のチェック
            comparison_result = ""
            for idx, existing_problem in enumerate(self.results):
                if existing_problem['問題番号'] == problem_number:
                    old_group = existing_problem['グループ番号']

                    # 過去と現在の結果に基づいてコメントを生成
                    if old_group in [1, 2] and group in [1, 2]:
                        comparison_result = "継続してよい学習できています"
                    elif old_group in [1, 2] and group not in [1, 2]:
                        comparison_result = "過去にできた問題です。復習が必要なようです。"
                    elif old_group not in [1, 2] and group in [1, 2]:
                        comparison_result = "とても良い学習ができています。自信をもって学習を継続しましょう。"
                    else:
                        comparison_result = "得点までもう少し、あなたの努力は確実に実っています。実力がついています。"

                    # 古いエントリを削除
                    self.results.pop(idx)
                    break

            problem_info = {
                '問題番号': problem_number,
                'グループ番号': group,
                '学習方法': self.groups[group],
                'コメント': comparison_result if comparison_result else comment,
                '教科': self.current_subject  # 教科を追加
            }
            self.results.append(problem_info)

            # 結果の保存と教科データの更新
            self.subjects[self.current_subject] = self.results

            # 分析結果のテキスト作成
            result_text = f"問題番号 {problem_number} は【グループ{group}】です。\n\n推奨される学習方法:\n{self.groups[group]}"

            # 得点率と完全解答率の計算
            if self.results:
                score_rate, perfect_rate = self.calculate_rates()
                result_text += f"\n\n得点率: {score_rate:.1f}%\n完全解答率: {perfect_rate:.1f}%"

            # 重複問題の場合、比較結果を追加
            if comparison_result:
                result_text += f"\n\n【重複問題の分析】\n{comparison_result}"

            return result_text
        except Exception as e:
            return f"分析中にエラーが発生しました: {str(e)}"

    def calculate_rates(self):
        """得点率と完全解答率を計算する"""
        if not self.results:
            return 0, 0

        total_problems = len(self.results)
        group_1_2_count = sum(1 for item in self.results if item['グループ番号'] in [1, 2])
        group_1_count = sum(1 for item in self.results if item['グループ番号'] == 1)

        score_rate = (group_1_2_count / total_problems) * 100 if total_problems > 0 else 0
        perfect_rate = (group_1_count / total_problems) * 100 if total_problems > 0 else 0

        return score_rate, perfect_rate

    def save_results(self):
        """すべての教科のデータを別々のExcelファイルとして一時ディレクトリに保存する"""
        try:
            if not self.subjects or all(not data for data in self.subjects.values()):
                return "保存するデータがありません。"

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # 一時ディレクトリを使用
            temp_dir = tempfile.gettempdir()
            file_data = []  # ファイルデータを格納するリスト

            # 教科が2つ以上ある場合、すべての教科のデータを個別に保存
            subject_count = len([s for s, data in self.subjects.items() if data])

            if subject_count >= 2:
                for subject, data in self.subjects.items():
                    if not data:  # 空のデータはスキップ
                        continue

                    # DataFrameを作成し、グループ番号で昇順に並び替え
                    df = pd.DataFrame(data)
                    # 教科列を追加（存在しない場合）
                    if '教科' not in df.columns:
                        df['教科'] = subject
                    df_sorted = df.sort_values('グループ番号')

                    # ファイル名に教科名を含める
                    file_name = f"学習問題分析結果_{subject}_{timestamp}.xlsx"
                    file_path = os.path.join(temp_dir, file_name)
                    
                    # Excelファイルを作成
                    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                        df_sorted.to_excel(writer, index=False, sheet_name=subject)
                        self._adjust_column_width(writer, df_sorted, subject)
                    
                    # BytesIO経由でファイルデータを取得
                    excel_data = self._get_excel_download_link(df_sorted, file_name, subject)
                    file_data.append((file_name, excel_data))

                # 全科目の統合ファイルも作成
                all_subjects_data = []
                for subject, data in self.subjects.items():
                    if not data:
                        continue

                    # 各レコードに教科名を追加
                    for record in data:
                        subject_record = record.copy()
                        if '教科' not in subject_record:
                            subject_record['教科'] = subject
                        all_subjects_data.append(subject_record)

                if all_subjects_data:
                    all_df = pd.DataFrame(all_subjects_data)
                    # 教科ごとにまとめて、グループ番号で整理
                    all_df_sorted = all_df.sort_values(['教科', 'グループ番号'])
                    all_file_name = f"学習問題分析結果_全教科統合_{timestamp}.xlsx"
                    
                    # Excelファイルを作成
                    all_file_path = os.path.join(temp_dir, all_file_name)
                    with pd.ExcelWriter(all_file_path, engine="openpyxl") as writer:
                        all_df_sorted.to_excel(writer, index=False, sheet_name="全教科統合")
                        self._adjust_column_width(writer, all_df_sorted, "全教科統合")
                    
                    # BytesIO経由でファイルデータを取得
                    all_excel_data = self._get_excel_download_link(all_df_sorted, all_file_name, "全教科統合")
                    file_data.append((all_file_name, all_excel_data))

                return file_data

            # 教科が1つだけの場合、現在の教科のデータだけを保存
            elif self.current_subject in self.subjects and self.subjects[self.current_subject]:
                # DataFrameを作成し、グループ番号で昇順に並び替え
                df = pd.DataFrame(self.subjects[self.current_subject])
                # 教科列を追加（存在しない場合）
                if '教科' not in df.columns:
                    df['教科'] = self.current_subject
                df_sorted = df.sort_values('グループ番号')

                # ファイル名に教科名を含める
                file_name = f"学習問題分析結果_{self.current_subject}_{timestamp}.xlsx"
                
                # BytesIO経由でファイルデータを取得
                excel_data = self._get_excel_download_link(df_sorted, file_name, self.current_subject)
                file_data.append((file_name, excel_data))
                
                return file_data
            else:
                return "保存するデータがありません。"
        except Exception as e:
            return f"保存中にエラーが発生しました: {str(e)}"

    def _get_excel_download_link(self, df, filename, sheet_name):
        """ExcelのダウンロードリンクのためのBase64エンコードされたデータを生成する"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            # ワークシートにアクセスしてカラム幅を調整
            worksheet = writer.sheets[sheet_name]
            for i, column in enumerate(df.columns):
                max_len = max(
                    len(str(column)),
                    df[column].astype(str).map(len).max()
                )
                # 特定の列には最小幅を設定
                if column in ['学習方法', 'コメント']:
                    max_len = max(max_len, 50)
                
                # A列から始まるので、i+1にする
                col_letter = worksheet.cell(row=1, column=i+1).column_letter
                # 列幅を設定（最大幅は100）
                col_width = min(max_len + 2, 100)
                worksheet.column_dimensions[col_letter].width = col_width
                
                # テキスト折り返しを設定（長文用）
                if column in ['学習方法', 'コメント']:
                    for row in range(1, len(df) + 2):
                        cell = worksheet.cell(row=row, column=i+1)
                        cell.alignment = cell.alignment.copy(wrapText=True)
        
        # バイナリデータの取得
        excel_binary = output.getvalue()
        
        # Base64エンコード
        b64 = base64.b64encode(excel_binary).decode()
        return b64

    def _adjust_column_width(self, writer, df, sheet_name):
        """Excelのカラム幅を調整する"""
        worksheet = writer.sheets[sheet_name]
        
        # 列ごとに最適な幅を計算
        for i, column in enumerate(df.columns):
            max_len = 0
            # カラム名の長さをチェック
            max_len = max(max_len, len(str(column)))
            
            # データの長さをチェック
            column_data = df[column].astype(str)
            for value in column_data:
                # 改行を含む場合は、行ごとに処理
                for line in str(value).split('\n'):
                    max_len = max(max_len, len(line))
            
            # 特定の列は最小幅を確保
            if column in ['学習方法', 'コメント']:
                max_len = max(max_len, 50)  # 長文用に幅を広げる
            
            # A列から始まるので、i+1にする
            col_letter = worksheet.cell(row=1, column=i+1).column_letter
            
            # 列幅を設定（最大幅は100）
            col_width = min(max_len + 2, 100)  # 少し余裕を持たせる
            worksheet.column_dimensions[col_letter].width = col_width
            
            # テキスト折り返しを設定（長文用）
            if column in ['学習方法', 'コメント']:
                for row in range(1, len(df) + 2):  # ヘッダー行 + データ行
                    cell = worksheet.cell(row=row, column=i+1)
                    cell.alignment = cell.alignment.copy(wrapText=True)

    def import_excel(self, uploaded_files):
        """アップロードされたExcelファイルからデータをインポートする"""
        try:
            if not uploaded_files:
                return "ファイルがアップロードされていません。"

            total_imported = 0
            imported_subjects = set()
            
            for uploaded_file in uploaded_files:
                # StreamlitのUploadedFileオブジェクトからデータを読み込む
                try:
                    df = pd.read_excel(uploaded_file, engine="openpyxl")
                except Exception as e:
                    continue

                # 必要なカラムが存在するか確認
                required_columns = ['問題番号', 'グループ番号', '学習方法']
                if not all(col in df.columns for col in required_columns):
                    continue

                # 教科列がある場合は、教科ごとにデータを振り分ける
                if '教科' in df.columns:
                    # 教科ごとにデータを分割
                    subject_groups = df.groupby('教科')

                    for subject, group_df in subject_groups:
                        # 教科列を除外せずにデータを取得
                        subject_data = group_df.to_dict('records')

                        # コメント列がない場合は追加
                        for item in subject_data:
                            if 'コメント' not in item:
                                item['コメント'] = ""

                        # 該当する教科のデータに追加
                        if subject not in self.subjects:
                            self.subjects[subject] = []

                        self.subjects[subject].extend(subject_data)
                        total_imported += len(subject_data)
                        imported_subjects.add(subject)

                else:
                    # 教科列がない場合は現在の教科に追加
                    imported_data = df.to_dict('records')

                    # コメント列がない場合は追加
                    for item in imported_data:
                        if 'コメント' not in item:
                            item['コメント'] = ""
                        # 教科列を追加
                        item['教科'] = self.current_subject

                    # 現在の教科のデータに追加
                    self.results.extend(imported_data)
                    self.subjects[self.current_subject] = self.results
                    total_imported += len(imported_data)
                    imported_subjects.add(self.current_subject)

            # 現在の教科を更新
            if self.current_subject in self.subjects:
                self.results = self.subjects[self.current_subject]

            if total_imported > 0:
                return f"{total_imported}件のデータを{len(imported_subjects)}教科にインポートしました。"
            else:
                return "インポートできるデータが見つかりませんでした。"
                
        except Exception as e:
            return f"インポート中にエラーが発生しました: {str(e)}"

    def get_subject_summary(self):
        """教科ごとのデータ数と状況をまとめたテキストを返す"""
        subject_info = []

        for subject, data in self.subjects.items():
            if data:  # データがある場合のみ
                score_rate = 0
                perfect_rate = 0

                # グループ1と2の問題数、グループ1の問題数を数える
                total_problems = len(data)
                group_1_2_count = sum(1 for item in data if item['グループ番号'] in [1, 2])
                group_1_count = sum(1 for item in data if item['グループ番号'] == 1)

                # 得点率と完全解答率を計算
                if total_problems > 0:
                    score_rate = (group_1_2_count / total_problems) * 100
                    perfect_rate = (group_1_count / total_problems) * 100

                subject_info.append(f"教科「{subject}」: {total_problems}問 (得点率: {score_rate:.1f}%, 完全解答率: {perfect_rate:.1f}%)")

        if subject_info:
            return "【分析済み教科の概要】\n" + "\n".join(subject_info)
        else:
            return "分析済みのデータがありません。"

# アプリケーションの初期化
def init_session_state():
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ProblemAnalyzer()
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'initial'  # 'initial', 'upload', 'analysis'
    if 'problem_number' not in st.session_state:
        st.session_state.problem_number = 1
    # 選択肢のリセット管理用
    if 'reset_selections' not in st.session_state:
        st.session_state.reset_selections = False

def reset_selection_states():
    """選択肢の状態をリセットする"""
    # 「正解」「不正解」以降の選択肢をリセット
    if 'correct' in st.session_state:
        current_correct = st.session_state.correct
        # 選択状態自体は残すが、その後の選択肢をリセット
        if 'hesitation' in st.session_state:
            del st.session_state.hesitation
        if 'cause' in st.session_state:
            del st.session_state.cause
        if 'mistake' in st.session_state:
            del st.session_state.mistake
        if 'knowledge' in st.session_state:
            del st.session_state.knowledge
        if 'experience' in st.session_state:
            del st.session_state.experience
        if 'issue' in st.session_state:
            del st.session_state.issue

def check_all_selections_made(correct):
    """すべての必要な選択肢が選択されているかチェックする"""
    if not correct:
        return False
    
    if correct == "正解":
        return 'hesitation' in st.session_state
    elif correct == "不正解":
        if 'cause' not in st.session_state:
            return False
            
        cause = st.session_state.cause
        if cause == "計算ミスやケアレスミス":
            return 'mistake' in st.session_state
        elif cause == "知識不足":
            return 'knowledge' in st.session_state
        elif cause == "解法が思いつかない":
            return 'experience' in st.session_state
        elif cause == "問題文の理解不足":
            return 'issue' in st.session_state
    
    return False



def main():
    st.set_page_config(page_title="学習問題分析プログラム", layout="wide")
    
    # セッション状態の初期化
    init_session_state()
    st.session_state.selected_option = None
    # リセットフラグがオンの場合、選択肢をリセットする
    if st.session_state.reset_selections:
        reset_selection_states()
        st.session_state.reset_selections = False
    
    st.title("学習問題分析プログラム")
    
    # 教科概要
    subject_summary = st.session_state.analyzer.get_subject_summary()
    st.text_area("教科概要", value=subject_summary, height=100, disabled=True)
    
    # 左右のカラムに分割
    left_col, right_col = st.columns([1, 3])
    
    with left_col:
        # 現在の教科表示
        st.text_input("現在の教科", value=st.session_state.analyzer.current_subject, disabled=True, key="current_subject_display")
        
        # 教科設定用フォーム
        with st.form(key="subject_form"):
            subject_input = st.text_input("教科名", key="subject_input")
            submit_subject = st.form_submit_button("教科を設定")
            
            if submit_subject:
                result = st.session_state.analyzer.set_subject(subject_input)
                st.success(result)
                # 教科概要を更新
                st.session_state.subject_summary = st.session_state.analyzer.get_subject_summary()
                # 選択肢をリセット
                st.session_state.reset_selections = True
                st.experimental_rerun()
        
        # アプリケーション切り替えボタン
        if st.button("別の教科を分析する"):
            st.session_state.analyzer.results = []
            st.session_state.app_stage = 'initial'
            st.session_state.analyzer.current_subject = "未設定"
            # 選択肢をリセット
            st.session_state.reset_selections = True
            st.session_state.radio_value = None
            st.experimental_rerun()
    
    # 初期画面
    if st.session_state.app_stage == 'initial':
        with right_col:
            st.header("データのインポート")
            st.write("教科を設定してからデータをインポートできます。")
            
            import_choice = st.radio("過去のデータをインポートしますか？", ["Yes", "No"], key="import_choice")
            
            if import_choice == "Yes":
                st.warning("使用するファイルは一度でアップロードしてください。", icon="⚠️")
                uploaded_files = st.file_uploader("分析データファイル (.xlsx)", type=["xlsx"], accept_multiple_files=True)
                
                if uploaded_files:
                    import_result = st.session_state.analyzer.import_excel(uploaded_files)
                    st.success(import_result)
                    # 教科概要を更新
                    st.text_area("教科概要", value=st.session_state.analyzer.get_subject_summary(), height=100, disabled=True)
                    
                    # 分析画面に移動
                    st.session_state.app_stage = 'analysis'
                    # 選択肢をリセット
                    st.session_state.reset_selections = True
                    st.experimental_rerun()
                    
            elif import_choice == "No":
                # 分析画面に移動
                st.session_state.app_stage = 'analysis'
                # 選択肢をリセット
                st.session_state.reset_selections = True
                st.experimental_rerun()
    
    # 分析画面
    elif st.session_state.app_stage == 'analysis':
        with right_col:
            st.header("問題分析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                problem_number = st.number_input("問題番号", min_value=1, value=st.session_state.problem_number, step=1)
                st.session_state.problem_number = problem_number
                
                
                # 正解状況の選択
                correct = st.radio("正解状況", ["正解", "不正解"], index = None,key="correct")
                
                # 正解の場合
                if correct == "正解":
                    hesitation = st.radio("解答プロセス", ["スムーズに解けた", "途中で手が止まった"],index = None, key="hesitation")
                    cause, mistake, knowledge, experience, issue = None, None, None, None, None
                
                # 不正解の場合
                elif correct == "不正解":
                    hesitation = None
                    cause = st.radio("間違いの原因", ["計算ミスやケアレスミス", "知識不足", "解法が思いつかない", "問題文の理解不足"],index = None, key="cause")
                    
                    # 計算ミスやケアレスミスの場合
                    if cause == "計算ミスやケアレスミス":
                        mistake = st.radio("計算ミスの傾向", ["初めてのミス", "同じミスを繰り返している"],index = None, key="mistake")
                        knowledge, experience, issue = None, None, None
                    
                    # 知識不足の場合
                    elif cause == "知識不足":
                        knowledge = st.radio("知識のレベル", ["基本事項の暗記ミス", "応用知識の不足"],index = None, key="knowledge")
                        mistake, experience, issue = None, None, None
                    
                    # 解法が思いつかないの場合
                    elif cause == "解法が思いつかない":
                        experience = st.radio("解法の経験", ["類似問題の経験あり", "全く経験がない"], index = None,key="experience")
                        mistake, knowledge, issue = None, None, None
                    
                    # 問題文の理解不足の場合
                    elif cause == "問題文の理解不足":
                        issue = st.radio("理解不足の詳細", ["用語の意味が分からない", "問題文の日本語が難しい", "解答を読んでも理解できない"], index = None,key="issue")
                        mistake, knowledge, experience = None, None, None
            
            with col2:
                # 分析実行ボタン（条件を満たした場合は自動的に実行）
                if st.session_state.analyzer.current_subject != "未設定" and check_all_selections_made(correct):
                    analysis_result = st.session_state.analyzer.analyze_problem(
                        st.session_state.analyzer.current_subject,
                        problem_number,
                        correct,
                        hesitation,
                        cause,
                        mistake,
                        knowledge,
                        experience,
                        issue
                    )
                    st.session_state.analysis_result = analysis_result
                
                # 分析結果の表示
                if 'analysis_result' in st.session_state:
                    st.text_area("分析結果", value=st.session_state.analysis_result, height=250, disabled=True)
            
            
            # ボタン行
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("結果をダウンロード"):
                    file_data = st.session_state.analyzer.save_results()
                    
                    if isinstance(file_data, list) and file_data:
                        for file_name, b64_data in file_data:
                            # ダウンロードリンクの生成
                            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}" download="{file_name}">Download {file_name}</a>'
                            st.markdown(href, unsafe_allow_html=True)
                    elif isinstance(file_data, str):
                        st.warning(file_data)
                    st.session_state.radio_value = None
                    correct = st.radio("正解状況", ["正解", "不正解"], index = None,key="correct")
            with col2:
                if st.button("続けて入力"):
                    # 問題番号を1つ増やし、他のフィールドをリセット
                    st.session_state.problem_number += 1
                    if 'analysis_result' in st.session_state:
                        del st.session_state.analysis_result
                    st.session_state.radio_value = None
                    correct = st.radio("正解状況", ["正解", "不正解"], index = None,key="correct")
                    st.experimental_rerun()


            with col3:
                if st.button("分析を終了"):
                    # 現在の教科の分析をクリアして初期画面に戻る
                    st.session_state.analyzer.results = []
                    st.session_state.analyzer.subjects[st.session_state.analyzer.current_subject] = []
                    st.session_state.app_stage = 'initial'
                    if 'analysis_result' in st.session_state:
                        del st.session_state.analysis_result
                    st.session_state.radio_value = None
                    correct = st.radio("正解状況", ["正解", "不正解"], index = None,key="correct")
                    st.experimental_rerun()
if __name__ == "__main__":
    main()
