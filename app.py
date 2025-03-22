import pandas as pd
import streamlit as st
import os
import io
import base64
from datetime import datetime

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
            5: "基礎知識の再暗記\n暗記カードやノートを使用して基本事項を再暗記する\n毎日繰り返し復習する",
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

    def analyze_problem(self, problem_number, correct, hesitation=None, cause=None, mistake=None, knowledge=None, experience=None, issue=None, comment=""):
        if not all([problem_number, correct]):
            return "問題番号と正解状況を選択してください。"

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
                        comparison_result = "得点までもう少し、あなたの努力は確実に変わっています。実力がついています。"

                    # 古いエントリを削除
                    self.results.pop(idx)
                    break

            problem_info = {
                '問題番号': problem_number,
                'グループ番号': group,
                '学習方法': self.groups[group],
                'コメント': comparison_result if comparison_result else comment
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

    def get_results_excel(self):
        """すべての教科のデータをExcelファイルとして返す"""
        try:
            if not self.subjects[self.current_subject]:
                return None, "保存するデータがありません。"

            # DataFrameを作成し、グループ番号で昇順に並び替え
            df = pd.DataFrame(self.subjects[self.current_subject])
            df_sorted = df.sort_values('グループ番号')

            # BytesIOオブジェクトにExcelを書き込む
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_sorted.to_excel(writer, index=False, sheet_name=self.current_subject)
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"学習問題分析結果_{self.current_subject}_{timestamp}.xlsx"
            
            return output.getvalue(), filename
        except Exception as e:
            return None, f"保存中にエラーが発生しました: {str(e)}"

    def import_excel(self, uploaded_file):
        """アップロードされたExcelファイルからデータをインポートする"""
        try:
            if uploaded_file is None:
                return "ファイルがアップロードされていません。"

            # Streamlitのアップロードファイルを読み込む
            df = pd.read_excel(uploaded_file, engine="openpyxl")

            # 必要なカラムが存在するか確認
            required_columns = ['問題番号', 'グループ番号', '学習方法']
            if not all(col in df.columns for col in required_columns):
                return "ファイル形式が正しくありません。必要なカラムが見つかりません。"

            # データをインポート
            imported_data = df.to_dict('records')

            # コメント列がない場合は追加
            for item in imported_data:
                if 'コメント' not in item:
                    item['コメント'] = ""

            # 現在の教科のデータに追加
            self.results.extend(imported_data)
            self.subjects[self.current_subject] = self.results

            return f"{len(imported_data)}件のデータをインポートしました。"
        except Exception as e:
            return f"インポート中にエラーが発生しました: {str(e)}"

def create_download_link(excel_data, filename):
    """エクセルファイルのダウンロードリンクを生成する"""
    if excel_data is None:
        return ""
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">ダウンロード</a>'
    return href

def main():
    st.set_page_config(page_title="学習問題分析プログラム", page_icon="📚", layout="wide")
    st.title("学習問題分析プログラム")
    
    # セッション状態の初期化
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ProblemAnalyzer()
    
    if 'is_analysis_screen' not in st.session_state:
        st.session_state.is_analysis_screen = False
        
    if 'problem_number' not in st.session_state:
        st.session_state.problem_number = 1
        
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = ""
        
    # サイドバーに現在の教科を表示
    st.sidebar.subheader("現在の教科")
    st.sidebar.info(st.session_state.analyzer.current_subject)
    
    # 教科設定部分
    with st.expander("教科を設定する", expanded=st.session_state.analyzer.current_subject == "未設定"):
        subject_col1, subject_col2 = st.columns([3, 1])
        with subject_col1:
            subject_name = st.text_input("教科名", key="subject_input")
        with subject_col2:
            if st.button("教科を設定", key="set_subject"):
                result = st.session_state.analyzer.set_subject(subject_name)
                st.success(result)
                # 教科が設定されたらセッションを更新
                st.experimental_rerun()
    
    # 教科が設定されていない場合は先に進めない
    if st.session_state.analyzer.current_subject == "未設定":
        st.warning("教科を設定してから次に進んでください。")
        return
    
    # データのインポート部分
    if not st.session_state.is_analysis_screen:
        st.header("データのインポート")
        import_choice = st.radio("過去のデータをインポートしますか？", ["はい", "いいえ"], key="import_choice")
        
        if import_choice == "はい":
            uploaded_file = st.file_uploader("分析データファイル (.xlsx)", type=["xlsx"])
            if uploaded_file is not None:
                import_result = st.session_state.analyzer.import_excel(uploaded_file)
                st.info(import_result)
                if "件のデータをインポートしました" in import_result:
                    st.success("インポートが完了しました。分析を続行できます。")
                    
        if st.button("分析を開始する", key="start_analysis"):
            st.session_state.is_analysis_screen = True
            st.experimental_rerun()
    
    # 分析画面
    else:
        st.header("問題分析")
        
        # 分析フォーム
        with st.form(key="analysis_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                problem_number = st.number_input("問題番号", min_value=1, value=st.session_state.problem_number, step=1)
                correct = st.radio("正解状況", ["正解", "不正解"], key="correct")
                
                # 正解の場合
                if correct == "正解":
                    hesitation = st.radio("解答プロセス", ["スムーズに解けた", "途中で手が止まった"], key="hesitation")
                    cause, mistake, knowledge, experience, issue = None, None, None, None, None
                
                # 不正解の場合
                else:
                    hesitation = None
                    cause = st.radio("間違いの原因", ["計算ミスやケアレスミス", "知識不足", "解法が思いつかない", "問題文の理解不足"], key="cause")
                    
                    # 原因に応じて追加の質問
                    if cause == "計算ミスやケアレスミス":
                        mistake = st.radio("計算ミスの傾向", ["初めてのミス", "同じミスを繰り返している"], key="mistake")
                        knowledge, experience, issue = None, None, None
                    elif cause == "知識不足":
                        knowledge = st.radio("知識のレベル", ["基本事項の暗記ミス", "応用知識の不足"], key="knowledge")
                        mistake, experience, issue = None, None, None
                    elif cause == "解法が思いつかない":
                        experience = st.radio("解法の経験", ["類似問題の経験あり", "全く経験がない"], key="experience")
                        mistake, knowledge, issue = None, None, None
                    elif cause == "問題文の理解不足":
                        issue = st.radio("理解不足の詳細", ["用語の意味が分からない", "問題文の日本語が難しい", "解答を読んでも理解できない"], key="issue")
                        mistake, knowledge, experience = None, None, None
            
            with col2:
                if st.session_state.analysis_result:
                    st.text_area("前回の分析結果", st.session_state.analysis_result, height=300, disabled=True)
            
            submit_button = st.form_submit_button("分析")
            
            if submit_button:
                # 分析実行
                result = st.session_state.analyzer.analyze_problem(
                    problem_number, correct, hesitation, cause, mistake, knowledge, experience, issue
                )
                st.session_state.analysis_result = result
                st.session_state.problem_number = problem_number + 1  # 次の問題番号を準備
                st.experimental_rerun()
        
        # 分析結果表示
        if st.session_state.analysis_result:
            st.subheader("分析結果")
            st.markdown(st.session_state.analysis_result.replace("\n", "<br>"), unsafe_allow_html=True)
        
        # 操作ボタン
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("結果をダウンロード"):
                excel_data, filename = st.session_state.analyzer.get_results_excel()
                if excel_data:
                    download_link = create_download_link(excel_data, filename)
                    st.markdown(download_link, unsafe_allow_html=True)
                else:
                    st.error("保存するデータがありません。")
        
        with col2:
            if st.button("続けて入力"):
                st.session_state.problem_number = problem_number + 1
                st.experimental_rerun()
        
        with col3:
            if st.button("分析を終了"):
                st.session_state.is_analysis_screen = False
                st.session_state.analysis_result = ""
                st.experimental_rerun()
        
        with col4:
            if st.button("別の教科を分析"):
                st.session_state.analyzer.results = []
                st.session_state.is_analysis_screen = False
                st.session_state.analysis_result = ""
                st.experimental_rerun()

if __name__ == "__main__":
    main()
