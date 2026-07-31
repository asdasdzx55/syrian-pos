using System;
using System.Windows;
using System.Windows.Input;
using AlmanzilSouriPos.Services;

namespace AlmanzilSouriPos
{
    public partial class MainWindow : Window
    {
        private readonly DatabaseService _dbService;
        private readonly PrinterService _printerService;

        public MainWindow()
        {
            InitializeComponent();
            _dbService = new DatabaseService();
            _printerService = new PrinterService();
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            switch (e.Key)
            {
                case Key.F1:
                    Shortcut_F1_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
                case Key.F2:
                    Shortcut_F2_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
                case Key.F3:
                    Shortcut_F3_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
                case Key.F5:
                    Shortcut_F5_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
                case Key.F6:
                    Shortcut_F6_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
                case Key.F12:
                    Shortcut_F12_Click(this, new RoutedEventArgs());
                    e.Handled = true;
                    break;
            }
        }

        private void Shortcut_F1_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F1: فتح نافذة البحث السريع عن المنتجات", "البحث السريع", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Shortcut_F2_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F2: تم تعليق الفاتورة الحالية بنجاح!", "تعليق الفاتورة", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Shortcut_F3_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F3: فتح قائمة الفواتير المعلقة واسترجاعها", "الفواتير المعلقة", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Shortcut_F5_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F5: إتمام الفاتورة كاش وطباعة الإيصال الحراري Xprinter 80mm", "تأكيد الدفع كاش", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Shortcut_F6_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F6: خيارات الدفع (فيزا / انستا باي / فودافون كاش / دفع متعدد)", "طرق الدفع", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Shortcut_F12_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("F12: الانتقال لشاشة استرجاع الفواتير والمرتجعات", "المرتجعات", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Sync_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("جاري المزامنة مع السيرفر الرئيسي (Laravel 11)...", "التزامن", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
